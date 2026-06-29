from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from meilisearch_python_sdk import AsyncClient
from datetime import datetime
from uuid import UUID

from qines_gai_backend.schemas.schema import T_Document, ReviewTask, ReviewResult

class ReviewRepository:
    def __init__(
        self,
        session: AsyncSession,
        meili_client: AsyncClient,
    ):
        self.session = session
        self.meili_client = meili_client

    async def create_task(
        self,
        *,
        input_doc_ids: list[str],
        knowhow_doc_ids: list[str],
    ) -> ReviewTask:
        task = ReviewTask(
            status="pending",
            total_rules=0,
            completed_rules=0,
            input_doc_ids=input_doc_ids,
            knowhow_doc_ids=knowhow_doc_ids,
        )

        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)

        return task

    async def get_task(
        self,
        *,
        task_id: UUID,
    ) -> ReviewTask | None:
        stmt = select(ReviewTask).where(ReviewTask.id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_task_status(
        self,
        *,
        task_id: UUID,
        status: str,
        error_message: str | None = None,
    ) -> None:
        task = await self.get_task(task_id=task_id)

        if task is None:
            return

        task.status = status
        task.error_message = error_message

        await self.session.commit()

    async def update_task_progress(
        self,
        *,
        task_id: UUID,
        total_rules: int | None = None,
        completed_rules: int | None = None,
        status: str | None = None,
    ) -> None:
        task = await self.get_task(task_id=task_id)

        if task is None:
            return

        if total_rules is not None:
            task.total_rules = total_rules

        if completed_rules is not None:
            task.completed_rules = completed_rules

        if status is not None:
            task.status = status

        await self.session.commit()

    async def bulk_create_results(
        self,
        *,
        task_id: UUID,
        results: list[dict],
    ) -> None:
        if not results:
            return

        rows = []

        for result in results:
            rows.append(
                ReviewResult(
                    task_id=task_id,
                    rule_id=result["rule_id"],
                    status=result["status"],
                    severity=result["severity"],
                    target=result.get("target"),
                    finding=result["finding"],
                    reason=result["reason"],
                    suggestion=result["suggestion"],
                    evidences=result.get("evidences", []),
                )
            )

        self.session.add_all(rows)
        await self.session.commit()

    async def list_results(
        self,
        *,
        task_id: UUID,
    ) -> list[ReviewResult]:
        stmt = (
            select(ReviewResult)
            .where(ReviewResult.task_id == task_id)
            .order_by(ReviewResult.id.asc())
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def get_meili_client(self) -> AsyncClient:
        return self.meili_client
    
    async def rollback(self) -> None:
        await self.session.rollback()

    def get_meili_index_name(self) -> str:
        # 実際の既存index名に合わせてください
        return "qines-gai"
    
    async def list_documents_by_role(
        self,
        document_role: str,
    ) -> list[T_Document]:
    
        stmt = (
            select(T_Document)
            .where(T_Document.document_role == document_role)
        )

        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())
    
    async def update_result_feedback(
        self,
        task_id: str,
        result_id: str,
        human_status: str | None = None,
        human_comment: str | None = None,
        corrected_finding: str | None = None,
        corrected_reason: str | None = None,
        corrected_suggestion: str | None = None,
    ) -> ReviewResult | None:
        stmt = select(ReviewResult).where(
            ReviewResult.id == result_id,
            ReviewResult.task_id == task_id,
        )

        result = await self.session.execute(stmt)
        review_result = result.scalar_one_or_none()

        if review_result is None:
            return None

        if human_status is not None:
            review_result.human_status = human_status

        if human_comment is not None:
            review_result.human_comment = human_comment

        if corrected_finding is not None:
            review_result.corrected_finding = corrected_finding

        if corrected_reason is not None:
            review_result.corrected_reason = corrected_reason

        if corrected_suggestion is not None:
            review_result.corrected_suggestion = corrected_suggestion

        review_result.reviewed_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(review_result)

        return review_result
    
    async def list_feedback_examples_by_rule_id(
        self,
        *,
        rule_id: str,
        limit_per_status: int = 2,
    ) -> list[ReviewResult]:
        """
        指定 rule_id に対する過去の人間レビュー済み結果を取得する。

        用途:
        - 次回レビュー時に、同じ rule_id の過去フィードバックをLLMプロンプトへ入れる
        - correct / false_positive / fixed をバランスよく取得する
        """

        target_statuses = [
            "correct",
            "false_positive",
            "fixed",
        ]

        feedback_examples: list[ReviewResult] = []

        for human_status in target_statuses:
            stmt = (
                select(ReviewResult)
                .where(ReviewResult.rule_id == rule_id)
                .where(ReviewResult.human_status == human_status)
                .order_by(ReviewResult.reviewed_at.desc(), ReviewResult.id.desc())
                .limit(limit_per_status)
            )

            result = await self.session.execute(stmt)
            feedback_examples.extend(list(result.scalars().all()))

        return feedback_examples
    
    async def get_task_by_id(self, task_id: str) -> ReviewTask | None:
        stmt = select(ReviewTask).where(ReviewTask.id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


    async def list_results_by_task_id(self, task_id: str) -> list[ReviewResult]:
        stmt = (
            select(ReviewResult)
            .where(ReviewResult.task_id == task_id)
            .order_by(ReviewResult.created_at.asc(), ReviewResult.id.asc())
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())