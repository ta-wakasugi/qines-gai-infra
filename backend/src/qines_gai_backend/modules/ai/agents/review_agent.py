# src/qines_gai_backend/modules/ai/agents/review_agent.py

from contextlib import contextmanager
from typing import Any

from langgraph.graph import END, START, StateGraph

from qines_gai_backend.logger_config import get_logger
logger = get_logger(__name__)

from pydantic import ValidationError
from langchain_core.messages import HumanMessage

from qines_gai_backend.modules.reviews.repositories import ReviewRepository

from .review_agent_prompt import build_review_messages

from .review_agent_schema import (
    ReviewAgentState,
    ReviewBatchOutput,
    ReviewFinding,
)
from .review_agent_search import (
    format_context_for_prompt,
    format_rules_for_prompt,
    load_input_contexts_from_meili,
    load_knowhow_rules_from_meili,
    split_batches,
    split_context_batches,
)

from qines_gai_backend.modules.reviews.feedback_prompt import (
    format_feedback_examples_for_prompt,
)


def _dump_pydantic_model(model: Any) -> dict:
    """
    Pydantic v1 / v2 両対応で dict に変換するためのヘルパー。

    Pydantic v2:
        model.model_dump()

    Pydantic v1:
        model.dict()
    """

    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()


@contextmanager
def _review_repository_context(db_session_factory):
    """
    LangGraphの各ノード内でDBセッションを短く開いて閉じるためのヘルパー。

    理由:
    - 長時間のAI処理中にDBセッションを開きっぱなしにしない
    - ノードごとにDB操作を完結させる
    """

    with db_session_factory() as db:
        yield ReviewRepository(db)
        
def _get_value(obj: Any, key: str) -> Any:
    """
    dict / Pydanticモデル の両方から値を取得する。
    """

    if isinstance(obj, dict):
        value = obj.get(key)
        if value is not None:
            return value

        metadata = obj.get("metadata")
        if isinstance(metadata, dict):
            return metadata.get(key)

        return None

    value = getattr(obj, key, None)
    if value is not None:
        return value

    if hasattr(obj, "model_dump"):
        data = obj.model_dump()
        value = data.get(key)
        if value is not None:
            return value

        metadata = data.get("metadata")
        if isinstance(metadata, dict):
            return metadata.get(key)

    if hasattr(obj, "dict"):
        data = obj.dict()
        value = data.get(key)
        if value is not None:
            return value

        metadata = data.get("metadata")
        if isinstance(metadata, dict):
            return metadata.get(key)

    return None


def _get_rule_id(rule: Any) -> str:
    rule_id = (
        _get_value(rule, "rule_id")
        or _get_value(rule, "chunk_id")
        or _get_value(rule, "id")
        or _get_value(rule, "doc_id")
        or _get_value(rule, "document_id")
    )

    if rule_id is None:
        if hasattr(rule, "model_dump"):
            keys = list(rule.model_dump().keys())
        elif isinstance(rule, dict):
            keys = list(rule.keys())
        else:
            keys = dir(rule)

        raise ValueError(f"rule_id を特定できません。rule type={type(rule)}, keys={keys}")

    return str(rule_id)

async def _attach_feedback_to_rules(
    *,
    rules: list[dict],
    repository: ReviewRepository,
    limit_per_status: int = 2,
) -> list[dict]:
    """
    各ノウハウルールに、同じ rule_id の過去人間レビュー結果を付与する。
    """

    rules_with_feedback: list[dict] = []

    for rule in rules:
        rule_id = _get_rule_id(rule)

        feedback_examples = await repository.list_feedback_examples_by_rule_id(
            rule_id=rule_id,
            limit_per_status=limit_per_status,
        )

        feedback_text = format_feedback_examples_for_prompt(feedback_examples)

        logger.info(
            "[review feedback] rule_id=%s feedback_count=%s",
            rule_id,
            len(feedback_examples),
        )

        rules_with_feedback.append(
            {
                "rule": rule,
                "rule_id": rule_id,
                "feedback_examples": feedback_text,
            }
        )

    return rules_with_feedback


def _format_rules_with_feedback_for_prompt(
    rules: list[dict],
) -> str:
    """
    feedback付きルールをプロンプト用文字列に変換する。
    """

    rule_blocks: list[str] = []

    for rule_with_feedback in rules:
        base_rule = rule_with_feedback["rule"]
        rule_id = rule_with_feedback["rule_id"]
        feedback_examples = rule_with_feedback.get(
            "feedback_examples",
            "過去の人間レビュー結果はありません。",
        )

        # 既存のノウハウ整形処理には、元の ReviewRule オブジェクトを渡す
        base_rule_text = format_rules_for_prompt([base_rule])

        rule_blocks.append(
            f"""
## rule_id: {rule_id}

### ベテランノウハウ

{base_rule_text}

### 過去の人間レビュー結果

{feedback_examples}
""".strip()
        )

    return "\n\n---\n\n".join(rule_blocks)


def build_review_graph(
    *,
    llm,
    repository: ReviewRepository,
    meili_client,
    meili_index_name: str,
):
    """
    自動レビュー用LangGraphを構築する。

    今回の処理単位:
        ノウハウルールバッチ × 入力データチャンクバッチ

    """

    structured_llm = llm.with_structured_output(ReviewBatchOutput)
    
    async def _invoke_review_with_retry(
            *,
            messages,
            max_retries: int = 2,
        ) -> ReviewBatchOutput:
            """
            LLMの structured output が ReviewBatchOutput のschemaに合わない場合、
            修正指示を追加して再実行する。

            主な対策:
            - finding / reason / suggestion 欠落
            - evidences だけ出力される不完全な finding
            - findings の要素が ReviewFinding schema に合わない
            """

            last_error: Exception | None = None
            current_messages = list(messages)

            for attempt in range(max_retries + 1):
                try:
                    return await structured_llm.ainvoke(current_messages)

                except ValidationError as e:
                    last_error = e

                    logger.warning(
                        "[review] structured output validation failed. attempt=%s/%s error=%s",
                        attempt + 1,
                        max_retries + 1,
                        str(e)[:1000],
                    )

                    retry_instruction = HumanMessage(
                        content=f"""
    前回の出力は ReviewBatchOutput の構造に違反していました。

    エラー内容:
    {str(e)}

    修正指示:
    - findings の各要素には必ず rule_id, status, severity, target, finding, reason, suggestion, evidences を含めてください。
    - finding, reason, suggestion は省略禁止です。
    - finding は「何が問題か」を具体的に書いてください。
    - reason は「なぜ問題なのか」を具体的に書いてください。
    - suggestion は「どのように修正すべきか」を具体的に書いてください。
    - 具体的な finding, reason, suggestion を書けない場合、その finding は出力せず findings=[] としてください。
    - evidence だけの不完全な finding は出力しないでください。
    - ReviewBatchOutput の構造に完全に従って再出力してください。
    """.strip()
                    )

                    current_messages = current_messages + [retry_instruction]

            if last_error is not None:
                raise last_error

            raise RuntimeError("Review structured output validation failed.")

    async def load_data_node(state: ReviewAgentState) -> ReviewAgentState:
        """
        最初に必要なデータをすべて取得するノード。

        ここで取得するもの:
        - レビュー観点となるノウハウルール
        - レビュー対象となる入力データ全文チャンク

        重要:
        - 入力データはキーワード検索しない
        - input_doc_ids に該当するチャンクを全件取得する
        """

        rules = await load_knowhow_rules_from_meili(
            meili_client=meili_client,
            index_name=meili_index_name,
            knowhow_doc_ids=state["knowhow_doc_ids"],
        )
        
        rules = await _attach_feedback_to_rules(
            rules=rules,
            repository=repository,
            limit_per_status=2,
        )

        input_contexts = await load_input_contexts_from_meili(
            meili_client=meili_client,
            index_name=meili_index_name,
            input_doc_ids=state["input_doc_ids"],
            document_role="review_input",
        )

        if not input_contexts:
            raise ValueError(
                "レビュー対象の入力データがMeilisearchから取得できませんでした。"
                " input_doc_ids と document_role=review_input の登録状況を確認してください。"
            )

        batch_size = state.get("batch_size", 5)

        rule_batches = split_batches(
            rules=rules,
            batch_size=batch_size,
        )

        context_batches = split_context_batches(
            input_contexts,
            max_chars=30000,
            max_chunks=30,
        )

        await repository.update_task_progress(
            task_id=state["task_id"],
            total_rules=len(rules),
            completed_rules=0,
            status="running",
        )
        
        logger.info(
            "[review] loaded data. rules=%s, input_contexts=%s, rule_batches=%s, context_batches=%s",
            len(rules),
            len(input_contexts),
            len(rule_batches),
            len(context_batches),
        )

        return {
            "rules": rules,
            "rule_batches": rule_batches,
            "input_contexts": input_contexts,
            "context_batches": context_batches,
            "current_rule_batch_index": 0,
            "current_context_batch_index": 0,
            "total_rules": len(rules),
            "completed_rules": 0,
            "last_findings": [],
            "error_message": None,
        }

    async def review_batch_node(state: ReviewAgentState) -> ReviewAgentState:
        """
        1回分のAIレビューを実行するノード。

        1回のレビュー対象:
        - 1つのルールバッチ
        - 1つの入力データチャンクバッチ

        つまり:
            Rule Batch i × Context Batch j
        をAIに渡す。
        """

        rule_batch_index = state["current_rule_batch_index"]
        context_batch_index = state["current_context_batch_index"]

        batch_rules = state["rule_batches"][rule_batch_index]
        batch_contexts = state["context_batches"][context_batch_index]

        rules_text = _format_rules_with_feedback_for_prompt(batch_rules)
        context_text = format_context_for_prompt(batch_contexts)

        messages = build_review_messages(
            rules_text=rules_text,
            input_context_text=context_text,
        )
        
        logger.info(
            "[review] reviewing batch. rule_batch_index=%s, context_batch_index=%s",
            state["current_rule_batch_index"],
            state["current_context_batch_index"],
        )

        output: ReviewBatchOutput = await  _invoke_review_with_retry(
            messages=messages,
            max_retries=2,
        )


        return {
            "last_findings": output.findings,
        }

    async def save_progress_node(state: ReviewAgentState) -> ReviewAgentState:
        """
        AIレビュー結果をDBに保存し、次に処理すべきバッチindexを進めるノード。

        重要:
        - Context Batch がまだ残っている場合:
            current_context_batch_index だけ進める

        - 現在の Rule Batch に対して全 Context Batch を見終わった場合:
            completed_rules を増やす
            current_rule_batch_index を進める
            current_context_batch_index を0に戻す
        """

        findings: list[ReviewFinding] = state.get("last_findings", [])

        result_rows: list[dict] = []

        for finding in findings:
            finding_dict = _dump_pydantic_model(finding)

            result_rows.append(
                {
                    "rule_id": finding_dict["rule_id"],
                    "status": finding_dict["status"],
                    "severity": finding_dict["severity"],
                    "target": finding_dict.get("target"),
                    "finding": finding_dict["finding"],
                    "reason": finding_dict["reason"],
                    "suggestion": finding_dict["suggestion"],
                    "evidences": finding_dict.get("evidences", []),
                }
            )

        current_rule_batch_index = state["current_rule_batch_index"]
        current_context_batch_index = state["current_context_batch_index"]

        rule_batches = state["rule_batches"]
        context_batches = state["context_batches"]

        next_rule_batch_index = current_rule_batch_index
        next_context_batch_index = current_context_batch_index + 1
        next_completed_rules = state["completed_rules"]

        finished_all_contexts_for_current_rule_batch = (
            next_context_batch_index >= len(context_batches)
        )

        if finished_all_contexts_for_current_rule_batch:
            completed_rule_count = len(rule_batches[current_rule_batch_index])
            next_completed_rules += completed_rule_count
            next_rule_batch_index += 1
            next_context_batch_index = 0

        await repository.bulk_create_results(
            task_id=state["task_id"],
            results=result_rows,
        )

        await repository.update_task_progress(
            task_id=state["task_id"],
            completed_rules=next_completed_rules,
        )

        return {
            "completed_rules": next_completed_rules,
            "current_rule_batch_index": next_rule_batch_index,
            "current_context_batch_index": next_context_batch_index,
            "last_findings": [],
        }

    async def finalize_node(state: ReviewAgentState) -> ReviewAgentState:
        """
        全レビュー完了時にタスクを completed にするノード。
        """
        await repository.update_task_progress(
            task_id=state["task_id"],
            completed_rules=state["total_rules"],
            status="completed",
        )

        return state

    def should_start_review(state: ReviewAgentState) -> str:
        """
        load_data の後、レビュー処理に進むか判定する。

        ルールが0件の場合:
            レビューする観点がないため finalize に進む

        ルールがある場合:
            review_batch に進む
        """

        if not state.get("rule_batches"):
            return "finalize"

        return "review_batch"

    def should_continue(state: ReviewAgentState) -> str:
        """
        save_progress の後、次のレビューが残っているか判定する。

        current_rule_batch_index が rule_batches の数以上になったら、
        全ルールバッチを処理済みなので finalize に進む。
        """

        if state["current_rule_batch_index"] >= len(state["rule_batches"]):
            return "finalize"

        return "review_batch"

    graph = StateGraph(ReviewAgentState)

    graph.add_node("load_data", load_data_node)
    graph.add_node("review_batch", review_batch_node)
    graph.add_node("save_progress", save_progress_node)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "load_data")

    graph.add_conditional_edges(
        "load_data",
        should_start_review,
        {
            "review_batch": "review_batch",
            "finalize": "finalize",
        },
    )

    graph.add_edge("review_batch", "save_progress")

    graph.add_conditional_edges(
        "save_progress",
        should_continue,
        {
            "review_batch": "review_batch",
            "finalize": "finalize",
        },
    )

    graph.add_edge("finalize", END)

    return graph.compile()