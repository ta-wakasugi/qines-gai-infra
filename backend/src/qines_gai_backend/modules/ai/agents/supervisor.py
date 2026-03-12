import os
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    SystemMessage,
    ToolMessage,
    trim_messages,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.config import RunnableConfig
from langfuse.callback import CallbackHandler
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langgraph.graph.state import END, START, CompiledStateGraph, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import Annotated, Any, AsyncGenerator, Literal

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.ai.agents.researcher import research_agent
from qines_gai_backend.modules.ai.llm_wrapper import LLMWrapper
from qines_gai_backend.modules.ai.mcp_client import (
    create_mcp_client,
    get_mcp_resources,
    get_mcp_tools,
)
from qines_gai_backend.modules.ai.tools import (
    create_artifact,
    edit_artifact,
    generate_test_case,
    get_artifact,
    get_document,
    list_documents_in_collection,
)
from qines_gai_backend.modules.collections.models import CollectionDetail
from qines_gai_backend.modules.conversations.models import (
    Artifact,
    ArtifactBase,
    MessageMetadata,
)

logger = get_logger(__name__)


SUPERVISOR_PROMPT = """\
あなたはQINeS-GAIと呼ばれるアシスタントです。
あなたがユーザーとの対話の中で扱う特徴的な概念は以下の２つです

## 扱う概念
### 1. コレクション 
１ファイルに相当する概念である`ドキュメント`の集合です。
ユーザーは一般的な情報ではなくレクションに含まれるドキュメントの情報を使ったやりとりを期待しています。
たとえば、ドキュメントの編集や内容の要約など、ユーザーの要望は多岐にわたることが想定されます。
ドキュメントをあなたが直接編集することはできません。必ず後述する概念である`アーティファクト`に変換してから編集し、その内容をユーザーに提示する必要があります。

### 2. アーティファクト
ユーザーとの会話中にアーティファクトを作成および参照できます。アーティファクトは、ユーザーが修正や再利用する可能性のある実質的で自己完結型のコンテンツであり、明確さのために別のUIウィンドウに表示されます。

#### 良いアーティファクトとは...
- 実質的なコンテンツ（15行以上）
- ユーザーが修正、反復、または所有権を持つ可能性が高いコンテンツ
- 会話のコンテキストなしで理解できる自己完結型の複雑なコンテンツ
- 最終的に会話外で使用することを意図したコンテンツ（例：レポート、メール、プレゼンテーション）
- 複数回参照または再利用される可能性が高いコンテンツ

#### アーティファクトを使用しないもの...
- 簡単な、情報提供的な、または短いコンテンツ（短いコードスニペット、数式、小さな例など）
- 主に説明的、教育的、または例示的なコンテンツ（概念を明確にするための例など）
- 既存のアーティファクトに対する提案、コメント、またはフィードバック
- 独立した作品を表さない会話的または説明的なコンテンツ
- 現在の会話のコンテキストに依存して有用なコンテンツ
- ユーザーによって修正または反復される可能性が低いコンテンツ
- ユーザーからの一回限りの質問と思われるリクエスト

#### 使用上の注意
- 特に要求されない限り、1メッセージにつき1つのアーティファクト
- 可能な場合はインラインコンテンツを優先（アーティファクトを使用しない）。不必要なアーティファクトの使用はユーザーにとって不自然な場合があります。
- あなたは簡潔さを重視し、会話内で効果的に提示できるコンテンツにアーティファクトを過剰に使用することは避けます。
- アーティファクトはUI上で表示されているため、あなたが内容を復唱する必要はありません。補足説明にとどめてください。
- アーティファクトへのリンクはユーザーへ提示してはいけません。
- 特に指定がない場合は、アーティファクトはマークダウン形式で生成してください。
- ユーザーから指示がない限り、アーティファクトのタイトルは変更してはいけません。
- アーティファクトに編集を加える際の編集操作は、ユーザーの指定した箇所以外にもアーティファクトの内容を考慮して整合性を保つようにしてください。
- 編集するアーティファクトに変更履歴を明記している箇所がある場合は、編集に伴って履歴を更新してください。

## 回答上の注意

- 一般的な情報の提供をせず、ReseachAgentの報告内容を優先的に提供してください。
- ユーザーにドキュメントの内容を提供するときは、内容を改変せず、かつ情報の抜け漏れがないようにしてください。
- あなたの思考過程の内容をユーザーに提供しないでください。
- なるべく平易な言葉で、わかりやすく伝えることを心がけてください。
- 説明が複雑になるときはmermaid記法で図示してください。
- mermaid構文では、ノード定義内のラベルは必ずダブルクォーテーション`"`で囲むように注意してください。例、A["hogehoge"]
- ドキュメントから直接的な情報が得られなかった場合は、その状況のみの回答を提供し、その他の情報は提供しないでください。
- アーティファクトの内容はユーザーに提示しないでください。
- ドキュメントIDは機微な情報なため、ユーザーにドキュメントIDを教えてはいけません。
- 新規アーティファクトを作成するまえに、過去のアーティファクトを編集すべきかどうかを考えてください。
- 使用後には作成したアーティファクトの概要をユーザーに伝えてください。
- アーティファクトの編集にツールを使用したあとは、影響範囲をユーザーに漏れなく的確にわかりやすく伝えてください。
- テストシナリオを生成する場合は、ツールを使用してください。あなたが追加で内容を考える必要はありません。ツール使用後は作成したテストシナリオの説明のみを簡潔にユーザーに提示してください。

## 使用できるツールについて
あなたはユーザーの要望に応えるために、複数のツールにアクセスできます。
ツールへの入力はユーザーに見えないようにしてください。

"""


class ArtifactOperation(BaseModel):
    type: Literal["edit", "create"] = Field(
        ...,
        description="成果物操作の種類。'edit'（編集）か'create'（新規作成）のどちらか",
    )
    target: str | None = Field(
        ...,
        description="操作対象の成果物。artifact_idとversionをハイフンでつないだ文字列で指定する。`type`が'create'の場合は`None`",
    )
    result: str = Field(
        ...,
        description="この操作の結果生成された成果物を特定するIDとバージョンのペアをハイフンでつないだ文字列",
    )


class AgentResponse(BaseModel):
    type: Literal["message", "artifact"] = Field(
        ..., description="エージェントの返答の種類（'message'の'artifact'どちらか）"
    )
    content: Artifact | AIMessageChunk = Field(
        ...,
        description="エージェントの返答のコンテンツ（`type`が'message'のときは`AIMessageChunk`, 'artifact'のときは`Artifact`）",
    )


class AgentState(BaseModel):
    messages: Annotated[list[BaseMessage], add_messages] = Field(
        ..., description="エージェントによって処理される会話履歴"
    )
    artifacts: dict[str, Artifact] | None = Field(
        default_factory=dict,
        description="エージェントがアクセスできる成果物。artifact_idとversionをハイフンでつないだ文字列をキーとし、Artifactオブジェクトをバリューとする辞書",
    )
    artifact_operations: list[ArtifactOperation] = Field(
        [], description="エージェントの行った成果物操作"
    )


class Agent:
    @classmethod
    @log_function_start_end
    async def create(
        cls,
        user_id: str,
        collection: CollectionDetail,
        mcp_config_path: Any = None,
    ):
        """Agentインスタンスを非同期で作成するファクトリーメソッド

        Args:
            user_id: 対話相手であるユーザーのID
            collection: 対話に使用する情報源
            mcp_config_path: MCP設定ファイルのパス（オプショナル）

        Returns:
            Agent: 初期化済みのAgentインスタンス
        """
        # 基本インスタンス作成
        instance = cls(user_id, collection)

        # MCP初期化
        if mcp_config_path and mcp_config_path.exists():
            try:
                # MCPクライアントを作成
                instance._mcp_client = create_mcp_client(mcp_config_path)

                # ツールを取得してエージェントのツールリストに追加
                mcp_tools = await get_mcp_tools(instance._mcp_client)
                if mcp_tools:
                    instance._tools.extend(mcp_tools)
                    logger.info(f"{len(mcp_tools)}個のMCPツールを追加しました")

                # リソースを取得してプロンプトに統合
                mcp_resources = await get_mcp_resources(instance._mcp_client)
                if mcp_resources:
                    logger.info(f"{len(mcp_resources)}個のMCPリソースを取得しました")
                    resource_text = "\n\n## MCPサーバーから提供された情報\n\n"
                    for resource in mcp_resources:
                        try:
                            uri = resource.metadata.get("uri", "")
                            name = resource.metadata.get("name", uri)
                            description = resource.metadata.get("description", "")
                            content = resource.as_string()

                            logger.info(f"Resource: {resource}")

                            resource_text += f"### {name}\n"
                            if description:
                                resource_text += f"{description}\n\n"
                            resource_text += f"```\n{content}\n```\n\n"
                        except Exception as e:
                            logger.warning(f"リソース {uri} の読み込みに失敗: {e}")
                            continue

                    instance._supervisor_prompt = SUPERVISOR_PROMPT + resource_text
                    logger.info("MCPリソースをスーパーバイザープロンプトに統合しました")

            except Exception as e:
                logger.exception(
                    f"MCPの初期化に失敗しました: {e}. MCPなしで続行します。"
                )
        elif mcp_config_path:
            logger.info("MCP設定ファイルが見つかりません。MCPなしで起動します。")

        return instance

    @log_function_start_end
    def __init__(
        self,
        user_id: str,
        collection: CollectionDetail,
    ):
        """ユーザーと対話を行い、要望を達成するエージェント

        Args:
            user_id: 対話相手であるユーザーのID
            collection: 対話に使用する情報源
        """
        self._config = {"configurable": {"thread_id": str(uuid4()), "user_id": user_id}}
        self._mcp_client = None
        self._supervisor_prompt = SUPERVISOR_PROMPT

        load_dotenv("/app/.env")
        USE_LANGFUSE = os.getenv("USE_LANGFUSE", "false")
        langfuse_handler = CallbackHandler(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
            user_id=os.getenv("LANGFUSE_USER_ID"),
        )
        USE_LANGFUSE = USE_LANGFUSE == "true"
        callbacks = [langfuse_handler] if USE_LANGFUSE else []
        self._config_langfuse = self._config.copy()
        self._config_langfuse["callbacks"] = callbacks

        # モデルのインスタンス化はユーティリティ関数を用意
        wrapper = LLMWrapper()
        self._llm = wrapper.get_llm(model_type=os.getenv("LLM_TYPE"), temperature=0)
        self._collection = collection

        self._tools = [
            get_artifact,
            create_artifact,
            edit_artifact,
            research_agent,
            get_document,
            list_documents_in_collection,
            generate_test_case,
        ]

        self._workflow = self._build_graph()

    @log_function_start_end
    def _build_graph(self) -> CompiledStateGraph:
        """エージェントのワークフローを初期化する"""
        graph = StateGraph(AgentState)
        graph.add_node("supervisor", self._supervisor)
        graph.add_node("tool", self._tool_node)
        graph.add_node("artifact_operator", self._artifact_operator)
        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges("supervisor", self._route_tools)
        graph.add_edge("tool", "supervisor")
        graph.add_edge("artifact_operator", "supervisor")

        return graph.compile(checkpointer=MemorySaver())

    # Node Functions
    @log_function_start_end
    async def _supervisor(
        self, state: AgentState, config: RunnableConfig
    ) -> dict[str, Any]:
        """ユーザーとやり取りし、他のエージェントを統率するSupervisorノード"""
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=self._supervisor_prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        chain = prompt | self._llm.bind_tools(
            self._tools
        )  # , parallel_tool_calls=False)
        response = await chain.ainvoke({"messages": state.messages}, config=config)
        return {"messages": response}

    @log_function_start_end
    async def _tool_node(self, state: AgentState, config: RunnableConfig):
        """ツールを実行するノード

        prebuilt.ToolNodeを使用すると平行実行されるため順次実行するためにノードを用意
        ツールの引数の中でエージェントに生成させない部分を注入する。
        """
        results = []
        tools_by_name = {tool.name: tool for tool in self._tools}

        for tool_call in state.messages[-1].tool_calls:
            if tool_call["name"] not in tools_by_name:
                return {
                    "messages": [
                        ToolMessage(
                            content="存在しないツールです。",
                            tool_call_id=tool_call["id"],
                        )
                    ]
                }
            match tool_call["name"]:
                # InjectedToolArgの実際の値を注入
                # 注入する値はJSON Serializableである必要があるため、直接変換できない値は個別対応
                # InjdectedToolArgが存在しないものはpass
                case "research_agent":
                    documents = [d.model_dump() for d in self._collection.documents]
                    tool_call["args"]["documents"] = documents
                case "get_artifact":
                    tool_call["args"]["source"] = [
                        a.model_dump() for a in state.artifacts.values()
                    ]
                case "get_document":
                    documents = [d.model_dump() for d in self._collection.documents]
                    tool_call["args"]["documents"] = documents
                    tool_call["args"]["source"] = [
                        a.model_dump() for a in state.artifacts.values()
                    ]
                case "list_documents_in_collection":
                    documents = [d.model_dump() for d in self._collection.documents]
                    tool_call["args"]["documents"] = documents
                case "generate_test_case":
                    documents = [d.model_dump() for d in self._collection.documents]
                    tool_call["args"]["documents"] = documents

            tool = tools_by_name[tool_call["name"]]
            logger.info(
                f"Starting tool `{tool_call['name']}` call (call_id={tool_call['id']})..."
            )
            result = await tool.ainvoke(tool_call, config=config)
            results.append(result)
            logger.info(
                f"Finished tool `{tool_call['name']}` call (call_id={tool_call['id']})."
            )

        return {"messages": results}

    @log_function_start_end
    async def _artifact_operator(self, state: AgentState, config: RunnableConfig):
        """成果物操作を行うノード"""
        results = []
        tools_by_name = {tool.name: tool for tool in self._tools}
        for tool_call in state.messages[-1].tool_calls:
            tool = tools_by_name[tool_call["name"]]

            if tool_call["name"] == "create_artifact":
                new_artifact_id = str(uuid4())
                tool_call["args"]["artifact_id"] = new_artifact_id
                result: ToolMessage = await tool.ainvoke(tool_call, config=config)
                results.append(result)

                new_artifact = result.artifact
                artifact_op = ArtifactOperation(
                    type="create",
                    target=None,
                    result=f"{new_artifact.id}-{new_artifact.version}",
                )
                state.artifact_operations.append(artifact_op)
                state.artifacts[f"{new_artifact.id}-{new_artifact.version}"] = (
                    new_artifact
                )
            elif tool_call["name"] == "get_document":
                tool_call["args"]["documents"] = [
                    d.model_dump() for d in self._collection.documents
                ]
                tool_call["args"]["source"] = [
                    a.model_dump() for a in state.artifacts.values()
                ]
                result: ToolMessage = await tool.ainvoke(tool_call, config=config)
                results.append(result)

                new_artifact = result.artifact
                if new_artifact is not None:
                    artifact_op = ArtifactOperation(
                        type="create",
                        target=None,
                        result=f"{new_artifact.id}-{new_artifact.version}",
                    )
                    state.artifact_operations.append(artifact_op)
                    state.artifacts[f"{new_artifact.id}-{new_artifact.version}"] = (
                        new_artifact
                    )
            else:
                # edit_artifactツールの場合は、影響範囲分析機能のためにコレクション情報を注入
                tool_call["args"]["source"] = [
                    a.model_dump() for a in state.artifacts.values()
                ]
                # edit_artifactツールに影響範囲分析用ドキュメント情報を注入
                if tool_call["name"] == "edit_artifact":
                    tool_call["args"]["documents"] = [
                        d.model_dump() for d in self._collection.documents
                    ]

                result: ToolMessage = await tool.ainvoke(tool_call, config=config)
                results.append(result)

                new_artifact = result.artifact
                artifact_op = ArtifactOperation(
                    type="edit",
                    target=f"{tool_call['args']['artifact_id']}-{tool_call['args']['version']}",
                    result=f"{new_artifact.id}-{new_artifact.version}",
                )
                state.artifact_operations.append(artifact_op)
                state.artifacts[f"{new_artifact.id}-{new_artifact.version}"] = (
                    new_artifact
                )
        return {
            "messages": results,
            "artifacts": state.artifacts,
            "artifact_operations": state.artifact_operations,
        }

    # Edge Functions
    @log_function_start_end
    async def _route_tools(self, state: AgentState, config: RunnableConfig) -> str:
        """Supervisorの返答によって分岐させるエッジ"""
        last_message = state.messages[-1]

        if isinstance(last_message, AIMessage) and len(last_message.tool_calls) > 0:
            if last_message.tool_calls[-1]["name"] in [
                "create_artifact",
                "edit_artifact",
                "get_document",
            ]:
                return "artifact_operator"
            else:
                return "tool"
        else:
            return END

    @log_function_start_end
    async def astream(
        self, messages: list[BaseMessage], artifacts: list[Artifact]
    ) -> AsyncGenerator[AgentResponse, None]:
        """会話履歴と成果物をもとにユーザーへの返答をストリームする関数

        Args:
            messages: ユーザーとエージェントの会話履歴
            artifacts: 会話によって生成された成果物のリスト

        Returns:
            AsyncGenerator[AgentReponse, None]: エージェントの生成したトークンを整形して返す
        """
        # モデルのコンテキスト長を超えないように、会話履歴を特定の長さでトリミング
        # 人間のメッセージが最初と最後の要素になるように設定
        # TODO: token_counterをtiktokenにしてモデルの使用するトークナイザに合わせる
        # TODO: max_tokensはモデルの最大コンテキスト長から算出（1/3程度）するように変更
        messages = trim_messages(
            messages,
            token_counter=len,
            max_tokens=1000,
            start_on="human",
            end_on="human",
            include_system=True,
            strategy="last",
        )

        artifact_dict = {
            f"{artifact.id}-{artifact.version}": artifact for artifact in artifacts
        }

        initial_state = AgentState(
            messages=messages,
            artifacts=artifact_dict,
            artifact_operations=[],
        )

        # 最終結果保存用
        buffered_ai_message = ""
        metadata = MessageMetadata(
            contexts=[],
            recommended_documents=[],
            generated_artifacts=[],
        )

        current_artifact: Artifact = None
        async for event in self._workflow.astream_events(
            initial_state,
            version="v2",
            config=self._config_langfuse,  # langfuse未使用時はself_configを使用
        ):
            if event["event"] == "on_chat_model_stream":
                if event["metadata"].get("langgraph_node") == "supervisor":
                    content = event["data"]["chunk"].content
                    buffered_ai_message += content
                    message = AIMessageChunk(content=content)
                    yield AgentResponse(
                        type="message",
                        content=message,
                    )
                if event["metadata"].get("langgraph_node") == "artifact_operator":
                    content = event["data"]["chunk"].content
                    if content:
                        current_artifact.content = content
                        yield AgentResponse(
                            type="artifact",
                            content=current_artifact,
                        )
            if event["event"] == "on_tool_start":
                if event["name"] == "create_artifact":
                    tool_input = event["data"]["input"]
                    current_artifact = Artifact(
                        id=tool_input["artifact_id"],
                        version=1,
                        title=tool_input["title"],
                        content="",
                    )
                if event["name"] == "edit_artifact":
                    tool_input = event["data"]["input"]
                    current_artifact = Artifact(
                        id=tool_input["artifact_id"],
                        version=tool_input["version"] + 1,
                        title=tool_input["title"],
                        content="",
                    )
            if event["event"] == "on_tool_end":
                if event["name"] == "research_agent":
                    tool_message: ToolMessage = event["data"]["output"]
                    researcher_state = tool_message.artifact
                    metadata.contexts.extend(researcher_state.contexts)
                    metadata.recommended_documents.extend(
                        researcher_state.recommendations
                        if researcher_state.recommendations
                        else []
                    )
                    message = AIMessageChunk(
                        content="",
                        additional_kwargs={"qines_gai_metadata": metadata.model_dump()},
                    )
                    yield AgentResponse(type="message", content=message)
                if event["name"] in ["create_artifact", "edit_artifact"]:
                    current_artifact = None
                    tool_message: ToolMessage = event["data"]["output"]
                    artifact = tool_message.artifact
                    metadata.generated_artifacts.append(
                        ArtifactBase(id=artifact.id, version=artifact.version)
                    )
                    message = AIMessageChunk(
                        content="",
                        additional_kwargs={"qines_gai_metadata": metadata.model_dump()},
                    )
                    yield AgentResponse(type="message", content=message)
                if event["name"] == "get_document":
                    tool_message: ToolMessage = event["data"]["output"]
                    artifact = tool_message.artifact
                    if artifact is not None:
                        current_artifact = artifact
                        metadata.generated_artifacts.append(
                            ArtifactBase(id=artifact.id, version=artifact.version)
                        )
                        yield AgentResponse(
                            type="artifact",
                            content=current_artifact,
                        )
                        message = AIMessageChunk(
                            content="",
                            additional_kwargs={
                                "qines_gai_metadata": metadata.model_dump()
                            },
                        )
                        yield AgentResponse(type="message", content=message)

        # DBに保存しやすいように生成した結果をStateの最後のメッセージにする
        # 途中で成果物生成が入った場合はState.messagesに重複した内容が入る
        generated_response = AIMessage(
            content=buffered_ai_message,
            additional_kwargs={"qines_gai_metadata": metadata.model_dump()},
        )
        await self._workflow.aupdate_state(
            self._config, {"messages": [generated_response]}
        )

    @log_function_start_end
    def get_state(self):
        """現在のエージェントの管理する情報を取得する"""
        return AgentState.model_validate(self._workflow.get_state(self._config).values)
