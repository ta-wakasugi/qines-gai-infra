import asyncio
import json
import os
from enum import Enum

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from pydantic import BaseModel, Field
from typing_extensions import Annotated, Any, Literal

from qines_gai_backend.config.dependencies.data_connection import (
    get_connection_manager,
    get_meili_client,
    get_s3_client,
)
from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.ai.llm_wrapper import LLMWrapper
from qines_gai_backend.modules.conversations.models import Artifact
from qines_gai_backend.modules.documents.models import DocumentBase
from qines_gai_backend.shared.storage_controller import download_from_storage

logger = get_logger(__name__)


class EditInfo(BaseModel):
    """編集情報モデル - 成果物の複数ヶ所編集をサポート"""

    start_line: int = Field(..., description="変更対象部分の開始行番号")
    end_line: int = Field(..., description="変更対象部分の終了行番号")
    target_content: str = Field(..., description="変更対象の内容")
    revised_content: str = Field(..., description="変更後の内容")
    operation: Literal["delete", "update", "add"] = Field(..., description="操作種別")


# //////////////////////////////////////////////////////////////////////
# エージェント用のツール群
# 共通のインターフェース（`ainvoke`）で呼び出すために、すべて非同期関数として定義する
# //////////////////////////////////////////////////////////////////////


@tool(parse_docstring=True, response_format="content_and_artifact")
@log_function_start_end
async def list_documents_in_collection(
    documents: Annotated[list[DocumentBase], InjectedToolArg],
):
    """コレクションに含まれるドキュメントのタイトルとIDの一覧化する。
    ユーザーの要望に応えるためにドキュメントに対する操作（閲覧、編集）が必要な場合に、操作対象のIDをこのツールを使用して獲得することで、特定のドキュメントへのアクセスが可能になる。

    Args:
        documents: ドキュメントリスト

    Returns:
        tuple[str, Artifact]:  指定された成果物が存在する場合はその内容。見つからない場合は作成された新規成果物を作成してその内容を返す'
    """
    documents_list_md = (
        f"# コレクションに含まれるドキュメント一覧（全{len(documents)}件）\n\n"
    )
    documents_list_md += "\n\n".join(
        [f"ID: {d.id}\nタイトル: {d.title}" for d in documents]
    )

    return documents_list_md, documents


@tool(parse_docstring=True, response_format="content_and_artifact")
@log_function_start_end
async def search_on_meilisearch(
    query: str,
    filter: Annotated[list[str], InjectedToolArg] = [],
) -> tuple[str, list[dict[str, Any]]]:
    """Meilisearchで全文検索を行い、チャンクを取得する。
        ここでチャンクとは、ドキュメントのコンテンツを一定の大きさで区切ったかたまりのことです。
        一つの検索結果のコンテンツは、一つのチャンクで構成されています。

    Args:
        query: 空白で区切られた検索クエリ。
        filter: 検索条件のリスト。Meilisearchのフィルタとして利用する文字列のリスト。

    Returns:
        str, list[dict[str, Any]: 検索結果のチャンクのJSON文字列と、検索結果のチャンクのリスト。
    """
    # 検索で十分な情報が得られなかった場合は、ページネーションするのではなく
    # クエリの再生成を行う方針。そのため、offset/limitは固定
    meili_client = await get_meili_client(get_connection_manager())
    index = meili_client.index("qines-gai")
    response = await index.search(query, limit=5, offset=0, filter=filter)

    # ==========================================
    # 【追加】Meilisearchの検索結果（生データ）をログに出力する
    # ==========================================
    logger.warning(f"🎯 検索キーワード: {query}")
    logger.warning(f"🎯 ヒット件数: {response.estimated_total_hits} 件")
    
    for i, hit in enumerate(response.hits):
        logger.warning(f"--- ヒット {i+1} 件目 ---")
        logger.warning(f"ID (チャンク): {hit.get('id')}")
        logger.warning(f"ファイル名: {hit.get('title')}")
        # ★一番重要な「チャンクのテキスト中身」を出力★
        logger.warning(f"中身(contents):\n{hit.get('contents', '※データなし')}")
    # ==========================================

    return json.dumps(response.hits, ensure_ascii=False, indent=2), response.hits


@tool(parse_docstring=True, response_format="content_and_artifact")
@log_function_start_end
async def get_adj_chunk(
    doc_id: str, chunk_num: int, direction: Literal["prev", "next"]
) -> tuple[str, list[dict[str, Any]]]:
    """Meilisearchの検索で得られたチャンクから、隣接したチャンクを取得する。
        ここでチャンクとは、ドキュメントのコンテンツを一定の大きさで区切ったかたまりのことです。
        一つの検索結果のコンテンツは、一つのチャンクで構成されています。

    Args:
        doc_id: ドキュメントを一意に識別するuuid。検索結果に含まれる。
        chunk_num: チャンクの順番を識別する値。検索結果に含まれる。
        direction: 追加で取得するチャンクの箇所(prev:一つ前のチャンク next: 一つ後ろのチャンク)

    Returns:
        str, list[dict[str, Any]: 取得したチャンクのJSON文字列と、取得したチャンク
    """
    meili_client = await get_meili_client(get_connection_manager())
    index = meili_client.index("qines-gai")

    if direction == "prev":
        target_chunk_num = chunk_num - 1
    else:
        target_chunk_num = chunk_num + 1

    if target_chunk_num < 0:
        return "チャンク番号は0以上である必要があります。", {}

    filter = [f"doc_id = {doc_id}", f"chunk_num = {target_chunk_num}"]
    search_results = await index.search(limit=1, filter=filter)

    return (
        json.dumps(search_results.hits, ensure_ascii=False, indent=2),
        search_results.hits,
    )


class TargetDocument(BaseModel):
    selected_document_id: str = Field(..., description="対象のドキュメントID")
    selected_document_title: str = Field(..., description="対象のドキュメントタイトル")
    selected_document_path: str = Field(
        ..., description="対象のドキュメントファイルパス"
    )


@tool(parse_docstring=True, response_format="content_and_artifact")
@log_function_start_end
async def get_document(
    document_id: str,
    documents: Annotated[list[DocumentBase], InjectedToolArg],
    source: Annotated[list[Artifact], InjectedToolArg],
    config: RunnableConfig,
) -> tuple[str, Artifact]:
    """ドキュメント一覧から、特定のドキュメントを取得する。成果物に変換されていない場合は成果物に変換して返却する。

    Args:
        document_id: コンテンツを取得したいドキュメントのID
        documents: ドキュメントリスト
        source: 編集可能なArtifactの一覧

    Returns:
        tuple[str, Artifact]:  指定された成果物が存在する場合はその内容。見つからない場合は作成された新規成果物を作成してその内容を返す'
    """
    s3_client = get_s3_client()
    id2doc = {d.id: d for d in documents}
    doc = id2doc.get(document_id)
    if not doc:
        return "指定されたドキュメントは存在しません。", None

    # 既存アーティファクトを検索（document_idと一致するartifact.idを持つものを探す）
    existing_artifact = next(
        (s for s in source if s.id == document_id),
        None
    )
    if existing_artifact:
        # 既存アーティファクトはartifact=Noneで返し、
        # artifact_operationsに追加されないようにする
        return (
            json.dumps(existing_artifact.model_dump(), ensure_ascii=False, indent=2),
            None,
        )
    else:
        # ファイルタイプをチェック（拡張子ベース、Markdownのみ編集可能）
        file_extension = doc.path.split(".")[-1].lower() if "." in doc.path else ""
        if file_extension != "md":
            return (
                f"エラー: '{doc.title}' は編集可能なテキストファイルではありません（拡張子: .{file_extension}）。このドキュメントの内容を参照するには`research_agent`ツールを使用してください。ユーザーに許可を取る必要はありません",
                None,
            )

        # 成果物作成
        # S3からドキュメント取得
        s3_client = get_s3_client()
        file_content = await download_from_storage(doc.path, s3_client)
        # 返却するアーティファクトを作成
        artifact = Artifact(
            id=doc.id,
            version=1,
            title=doc.title,
            content=file_content,
        )
        return json.dumps(artifact.model_dump(), ensure_ascii=False, indent=2), artifact


@tool(parse_docstring=True, response_format="content_and_artifact")
@log_function_start_end
async def get_artifact(
    source: Annotated[list[Artifact], InjectedToolArg],
    artifact_id: str,
    version: int,
) -> tuple[str, None]:
    """成果物一覧から、特定の成果物を取得する
        - 過去に生成したアーティファクトを参照できます。

    Args:
        source: 成果物一覧
        artifact_id: 取得したい成果物のID
        version: 取得したい成果物のバージョン

    Returns:
        tuple[str, None]: 指定された成果物が存在する場合はその内容。見つからない場合は'指定された成果物が見つかりません。
    """
    source = {(s.id, s.version): s for s in source}
    artifact = source.get((artifact_id, version), None)
    if artifact:
        return json.dumps(artifact.model_dump(), indent=2, ensure_ascii=False), None
    else:
        return "指定された成果物が見つかりません。", None


@tool(parse_docstring=True, response_format="content_and_artifact")
@log_function_start_end
async def edit_artifact(
    artifact_id: str,
    version: int,
    edits: list[EditInfo],
    source: Annotated[list[Artifact], InjectedToolArg],
    title: str,
    config: RunnableConfig,
    # supervisorから注入されるコレクション内のドキュメント情報
    documents: Annotated[list[DocumentBase], InjectedToolArg],
) -> tuple[str, Artifact]:
    """指定された成果物を複数ヶ所編集し、編集後の影響範囲を分析する
        - 過去に生成したアーティファクトを編集します。
        - アーティファクトの変更内容はユーザーの目的を達成する内容でなければいけません。
        - 編集したアーティファクトは決して省略せず、すべてをユーザーに返さなければいけません。
        - 編集完了後、コレクション情報を基に影響範囲を自動分析し、結果をユーザーに報告します。
        - アーティファクトのコンテンツを変更する場合はひとつの変更内容ごとに以下の内容を指定してください。
            - start_line: 編集対象のアーティファクトのコンテンツ内の変更対象部分のはじめの行番号
            - end_line: 編集対象のアーティファクトのコンテンツ内の変更対象部分のおわりの行番号
            - target_content: 変更前のコンテンツのstart_lineからend_lineに該当するコンテンツを抜き出したもの
            - revised_content: target_contentを新たに置換するコンテンツの内容
            - operation: 変更種別。"delete"または"update"または"add"
        - 編集対象がマークダウンで冒頭```markdownが記載されている場合、その表記を削除しないでください。

    Args:
        artifact_id: 編集対象のArtifactのID
        version: 編集対象のArtifactのバージョン
        edits: 編集操作のリスト。各EditInfoには編集対象の詳細情報が含まれる。
        source: 編集可能なArtifactの一覧
        title: 編集にともなってタイトルも変更する場合は、そのタイトル。変更しない場合はもとのタイトル。
        documents: 影響範囲分析用のコレクション内ドキュメント情報

    Returns:
        tuple[str, Artifact]: 更新されたArtifact。指定された成果物が見つからない場合は'指定された成果物が見つかりません。'
    """
    if not edits:
        return "編集操作が指定されていません。", None

    # 対象のアーティファクトを特定
    source_dict = {f"{s.id}-{s.version}": s for s in source}
    target_artifact = source_dict.get(f"{artifact_id}-{version}", None)
    if not target_artifact:
        return "指定された成果物が見つかりません。", None

    wrapper = LLMWrapper()
    llm = wrapper.get_llm(model_type=os.getenv("LLM_TYPE"), temperature=0)

    # 複数の編集操作を統合したプロンプトを作成
    edit_instructions = []
    for i, edit in enumerate(edits, 1):
        operation_type = {"delete": "削除", "update": "更新", "add": "追加"}.get(
            edit.operation, edit.operation
        )

        edit_instructions.append(
            f"""
編集操作 {i} ({operation_type}):
- 対象行: {edit.start_line}行目から{edit.end_line}行目
- 変更対象内容: {edit.target_content}
- 変更後内容: {edit.revised_content}"""
        )

    prompt = PromptTemplate.from_template(
        """\
編集対象のドキュメントのコンテンツに対して、以下の複数の編集操作を順次適用し、編集後のコンテンツを作成してください。
編集後のコンテンツには、編集対象のドキュメントの内容に編集操作一覧の編集を加えた結果を省略せずにすべて返してください。
ドキュメントの内容の編集操作の対象でない部分も、決して省略せずに編集結果に含めてください。
編集後のコンテンツにはアーティファクトのタイトルを付け加えないでください。
編集操作によりコンテンツの他の部分にも影響がある場合は、該当部分も整合性確保のため変更してください。
編集後にはコンテンツの更新履歴の部分に履歴を追加する変更も行ってください。
編集後のコンテンツはそのままドキュメントとなるため、加えた変更の説明等やコンテンツ作成前後の報告は行わないでください。

編集対象ドキュメント:{title}
内容：
{content}

編集操作一覧:
{edit_instructions}

編集結果:"""
    )

    chain = prompt | llm
    result = await chain.ainvoke(
        {
            "title": target_artifact.title,
            "content": target_artifact.content,
            "edit_instructions": "\n".join(edit_instructions),
        },
        config=config,
    )

    # 編集後の影響範囲をAIが分析してユーザーに報告
    impact_analysis = ""
    if documents:
        # ドキュメント情報からsummary情報を取得してJSON形式に変換
        documents_info = []
        for doc in documents:
            doc_info = {"id": doc.id, "title": doc.title, "summary": doc.summary}
            documents_info.append(doc_info)

        # JSON文字列に変換
        description_text = json.dumps(documents_info, ensure_ascii=False, indent=2)
        logger.info(f"[edit_artifact] Generated description_text: {description_text}")

        if description_text and description_text.strip():
            # 編集内容の詳細を作成
            edit_details = []
            edit_details.append(f"タイトル: {title}")
            edit_details.append(f"編集操作数: {len(edits)}件")
            for i, edit in enumerate(edits, 1):
                operation_type = {
                    "delete": "削除",
                    "update": "更新",
                    "add": "追加",
                }.get(edit.operation, edit.operation)
                edit_details.append(
                    f"編集{i}: {operation_type} ({edit.start_line}-{edit.end_line}行目) - {edit.target_content}..."
                )
            edit_summary = "\n".join(edit_details)

            # 影響範囲分析用プロンプトを作成
            impact_prompt = PromptTemplate.from_template(
                """\
以下の編集内容について、コレクション全体への影響範囲を分析してください。

コレクション情報:
{description_text}

編集内容:
{edit_summary}

影響範囲分析:
- 編集内容によって変更を加えた文言や値をもとに、コレクション情報から整合性をとるべき箇所を教えてください。
- 整合性を取るべき箇所はコレクション内の他のドキュメントにもある可能性があります。ドキュメント名と影響範囲、修正提案も含め実用的な分析結果を提供してください。
- 影響範囲は、次にユーザーから修正指示が来たときにすぐに修正できるレベルの具体性を持たせたうえで、ですます口調で簡潔にユーザーに提示してください。。
- 特に注意すべき点や確認が必要な箇所があれば指摘してください。
- 影響を受けるドキュメントがない場合は、""今回の修正では影響を受けるドキュメントはありません。""と答えてください。

フォーマット：
### 編集内容
- 編集内容を言語化したもの
### 影響範囲
**ドキュメント名**
- 影響を受ける部分と修正提案

"""
            )

            impact_chain = impact_prompt | llm
            # Artifactパネルに表示されるのを防ぐため、成果物編集とは別configで実行
            impact_config = RunnableConfig(tags=["impact_analysis"])
            impact_result = await impact_chain.ainvoke(
                {
                    "description_text": description_text,
                    "edit_summary": edit_summary,
                },
                config=impact_config,
            )
            impact_analysis = impact_result.content

    # 編集結果のアーティファクトを作成
    artifact = Artifact(
        id=target_artifact.id,
        version=target_artifact.version + 1,
        title=title,
        content=result.content,
    )

    # 返却内容に影響範囲分析結果を含める
    response_content = json.dumps(artifact.model_dump(), ensure_ascii=False, indent=2)
    if impact_analysis:
        response_content += f"\n\n## 影響範囲分析\n{impact_analysis}"

    return response_content, artifact


@tool(parse_docstring=True, response_format="content_and_artifact")
@log_function_start_end
async def create_artifact(
    artifact_id: Annotated[str, InjectedToolArg],
    title: str,
    content: str,
    config: RunnableConfig,
) -> tuple[str, Artifact]:
    """新規成果物を作成する
        - 新規アーティファクトを作成します。
        - アーティファクトのコンテンツはユーザーの目的を達成する内容でなければいけません。

    Args:
        artifact_id: 生成する成果物のID
        title: 成果物のタイトル
        content: 成果物のコンテンツ

    Returns:
        Artifact: 作成された新規成果物
    """

    # Supervisorがすでにcontentをつくっているが、UIの右パネルに振り分けるために再生成
    # ToolCallChunkをストリームできれば不要
    wrapper = LLMWrapper()
    llm = wrapper.get_llm(model_type=os.getenv("LLM_TYPE"), temperature=0)
    prompt = PromptTemplate.from_template(
        """\
以下の目的を達成できるように、調査結果の内容をつかってドキュメントを作成してください。
ドキュメントはそれ単体で理解できるように構成する必要があります。
アーティファクト内の情報元の提示はドキュメント内では行わないでください。
ドキュメントのコンテンツのみを出力してください。「以下に〜作成しました。」などの文言は必要ありません。
また、```markdown`や` ``` `などのマークダウンコードブロックの表記は追加しないでください。

タイトル: {title}
コンテンツ: {content}

"""
    )

    chain = prompt | llm
    result = await chain.ainvoke(
        {
            "title": title,
            "content": content,
        },
        config=config,
    )

    artifact = Artifact(id=artifact_id, version=1, title=title, content=result.content)
    return json.dumps(artifact.model_dump(), ensure_ascii=False, indent=2), artifact


class TestScenario(BaseModel):
    id: str = Field(..., description="テストシナリオID", examples=["SCT-001"])
    name: str = Field(
        ..., description="シナリオ名（簡潔に）", examples=["手動上昇・停止動作"]
    )
    object: str = Field(
        ...,
        description="目的や確認内容（1文程度）",
        examples=["各モードにおける手動上昇開始、途中停止、全閉時停止"],
    )
    prior_conditions: str = Field(
        ..., description="事前条件", examples=["・ECUをIDLE状態に遷移させる"]
    )
    post_conditions: str = Field(
        ..., description="事後条件", examples=["・検証環境を全てリセットする"]
    )


class TestScenarios(BaseModel):
    items: list[TestScenario] = Field(..., description="List of test scenarios")


class TestType(str, Enum):
    requirement_based = "要求ベース"
    interface_based = "インタフェース"
    fault_injection_based = "障害注入"
    resource_usage_based = "リソース使用状況"
    others = "その他"

    class Config:
        use_enum_values = True  # Pydantic用設定（モデル側で反映される）


class TestCaseDerivationTechnique(str, Enum):
    requirement = "要求"
    equivalence = "同値"
    boundary_value = "境界値"
    estimation = "推定"

    class Config:
        use_enum_values = True


class SignalConfirmationAspect(BaseModel):
    signal_aspect_description: str = Field(
        ...,
        description="計測信号の確認項目",
        examples=[
            "Motor_Control(xxx上のCAN信号)が右記期待値であることを確認する",
            "LED_Status(xxx上のCAN信号)が右記期待値であることを確認する",
            "Window_Position(xxx上のCAN信号)が右記期待値であることを確認する",
        ],
    )
    allowable_range: str = Field(..., description="許容範囲", examples=["±0.5%", "-"])
    expected_value: float = Field(..., description="期待値", examples=[0, 1, 80])


class ConfirmationAspect(BaseModel):
    confirmation_aspect_description: str = Field(
        ...,
        description="確認観点",
        examples=[
            "Motorが回転率を受信していることを確認する",
            "Body ECUが通常のLED表示を受信していることを確認する",
            "各センサーが信号を正常に出力していることを確認する",
            "Body ECUが異常時のLED表示及び挟み込み検知情報を受信していることを確認する",
        ],
    )

    signal_confirmation_aspects: list[SignalConfirmationAspect] = Field(
        ..., description="計測信号の確認項目のリスト。最低１つ以上。", min_length=1
    )


class SignalManipulationProcedure(BaseModel):
    signal_manipulation_procedure: str = Field(
        ...,
        description="プラント/CANによる信号の操作手順",
        examples=[
            "SW_UpDown(SW_UpDown SensorのCAN信号)を右記値で出力する",
            "Window_Position(Position SensorのCAN信号)を右記値で出力する",
            "入力なし",
            "System_Check(Body ECUのCAN信号)を右記値で出力する",
        ],
    )
    input_values: float = Field(..., description="入力値", examples=[0, 1, 3.5])
    execution_time: float = Field(
        ..., description="実施時間[s]", examples=[0.5, 3.5, 4]
    )


class VerificationProcedure(BaseModel):
    procedure_description: str = Field(
        ...,
        description="検証手順",
        examples=[
            "SW_UpDown SensorがSW_UpDownを1で出力する",
            "入力なし",
            "Current SensorがMotor_Currentを3.0Aより大きい値で出力する",
        ],
    )
    signal_manipulation_procedures: list[SignalManipulationProcedure] = Field(
        ..., description="プラント/CANによる信号の操作手順"
    )
    confirmation_aspects: list[ConfirmationAspect] = Field(
        ..., description="確認観点のリスト。最低１つ以上。", min_length=1
    )


class TestStep(BaseModel):
    test_case_id: str = Field(..., description="テストケースID", examples=["SCT-001-1"])
    test_type: TestType = Field(..., description="テスト手法")
    derivation_technique: TestCaseDerivationTechnique = Field(
        ..., description="テストケース導出手法"
    )
    request_id: str = Field(..., description="要求ID")
    step_description: str = Field(
        ...,
        description="テストステップ",
        examples=[
            "「IDLE」から「MANUAL UP」への遷移",
            "「MANUAL_UP」中の動作",
        ],
    )
    verification_procedures: list[VerificationProcedure] = Field(
        ..., description="検証手順"
    )


class TestSteps(BaseModel):
    items: list[TestStep] = Field(..., description="テストステップ")


@tool(parse_docstring=True, response_format="content_and_artifact")
@log_function_start_end
async def generate_test_case(
    document_id: str, documents: Annotated[list[DocumentBase], InjectedToolArg]
):
    """指定されたソフトウェアの仕様書に対してテストケースを生成する。
        - ドキュメントがソフトウェアの仕様書である場合、ユーザーからテストケースの作成依頼があった場合に使用できます。
        - JSONで帰ってくるため、わかりやすくアーティファクトに変換したうえでユーザーに提示しなくてはいけません。

    Args:
        document_id: ソフトウェアの仕様書として作成されたドキュメントのID。中身を確認して、ソフトウェアの仕様書であるか確認してから使用する必要がある。
        documents: コレクションに含まれるドキュメントのリスト

    Returns:
        tuple[str, Artifact]: 生成されたテストケース。ユーザーに提示する場合は、アーティファクトに変換にすることを推奨します。
    """
    # S3からドキュメント取得
    s3_client = get_s3_client()
    id2path = {d.id: d.path for d in documents}
    path = id2path.get(document_id)
    if not path:
        return "指定されたドキュメントが見つかりません。", None
    input_spec = await download_from_storage(path, s3_client)

    wrapper = LLMWrapper()
    model = wrapper.get_llm(model_type=os.getenv("LLM_TYPE"), temperature=0)
    system_input = """\
あなたは、車載ソフトウェアのテスト仕様書を解析する専門家です。
あなたの役割は、与えられた仕様書に基づいて、以下を行うことです：   
0. 仕様書から入力値、出力値の信号名の抽出
1. 単体テスト項目の作成
2. 抽出したテスト項目をテストシナリオとしてテスト仕様書に埋め込む
3. テスト仕様書の評価
4. テスト仕様書の修正
"""

    async def create_test_scenarios(input_spec: str) -> list[TestScenario]:
        user_input = """\
以下の仕様書をもとに、結合テストシナリオを作成してください。

仕様書: {input_spec}
- 出力は JSON 形式で、次の構造を持つリストとしてください：
- id: テストシナリオID
- name: シナリオ名（簡潔に）
- object: テスト目的（簡潔に）
"""
        model_with_structure = wrapper.get_structured_llm(
            TestScenarios, llm_instance=model
        )
        prompt = ChatPromptTemplate.from_messages(
            [("system", system_input), ("human", user_input)]
        )
        chain = prompt | model_with_structure
        response = await chain.ainvoke({"input_spec": input_spec})

        return response.items

    async def create_test_steps(
        test_scenario: str, input_spec: str
    ) -> list[TestStep]:
        user_input = """\
以下の結合テストシナリオに関して、テストステップを作成してください。

テストシナリオ: {test_scenario}
仕様書: {input_spec}
"""
        model_with_structure = wrapper.get_structured_llm(TestSteps, llm_instance=model)
        prompt = ChatPromptTemplate.from_messages(
            [("system", system_input), ("human", user_input)]
        )
        chain = prompt | model_with_structure
        output = await chain.ainvoke(
            {"test_scenario": test_scenario, "input_spec": input_spec}
        )
        return output.items

    async def organize_test_case(scenario: TestScenario, input_spec: str):
        test_scenario_md = f"## テストシナリオ\n\nテストID: {scenario.id}\n\nテストシナリオ名: {scenario.name}\n\nテスト目的: {scenario.object}\n\n事前条件: {scenario.prior_conditions}\n\n事後条件: {scenario.post_conditions}\n"
        test_steps = await create_test_steps(test_scenario_md, input_spec)
        _scenario = scenario.model_dump()
        _scenario["test_steps"] = [i.model_dump() for i in test_steps]
        return _scenario

    try:
        test_scenarios = await create_test_scenarios(input_spec)
        test_scenarios_with_steps = await asyncio.gather(
            *[organize_test_case(scenario, input_spec) for scenario in test_scenarios]
        )

        return (
            json.dumps(test_scenarios_with_steps, ensure_ascii=False, indent=2),
            test_scenarios_with_steps,
        )
    except Exception as e:
        logger.error(f"テストケース生成中にエラーが発生しました: {e}")
        return f"テストケース生成中にエラーが発生しました: {e}", None
