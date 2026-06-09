# src/qines_gai_backend/modules/ai/agents/review_agent.py

from contextlib import contextmanager
from typing import Any

from langgraph.graph import END, START, StateGraph

from qines_gai_backend.logger_config import get_logger
logger = get_logger(__name__)

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

        rules_text = format_rules_for_prompt(batch_rules)
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

        output: ReviewBatchOutput = await structured_llm.ainvoke(messages)

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