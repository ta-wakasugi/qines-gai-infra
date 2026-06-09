from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from meilisearch_python_sdk import AsyncClient
from uuid import UUID

from qines_gai_backend.schemas.schema import ReviewTask, ReviewResult

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