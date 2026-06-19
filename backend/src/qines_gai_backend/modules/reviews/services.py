import os
from qines_gai_backend.modules.ai.agents.review_agent import build_review_graph
from qines_gai_backend.modules.reviews.repositories import ReviewRepository

from qines_gai_backend.modules.ai.agents.review_agent_schema import (
    Evidence,
    ReviewBatchOutput,
    ReviewFinding,
)

from qines_gai_backend.modules.ai.llm_wrapper import LLMWrapper
from fastapi import HTTPException

from qines_gai_backend.logger_config import get_logger

logger = get_logger(__name__)

class ReviewService:
    def __init__(self, repository: ReviewRepository):
        self.repository = repository

    async def create_review_task(
        self,
        *,
        input_doc_ids: list[str],
        knowhow_doc_ids: list[str],
    ):
        return await self.repository.create_task(
            input_doc_ids=input_doc_ids,
            knowhow_doc_ids=knowhow_doc_ids,
        )
    
    async def run_review_task(
        self,
        *,
        task_id: int,
        input_doc_ids: list[str],
        knowhow_doc_ids: list[str],
        batch_size: int = 5,
    ) -> None:
        """
        LangGraphのレビュー処理を実行する。

        注意:
        llm は既存のAIService / LLM Wrapper の作り方に合わせて渡す想定。
        """
        
        logger.info(
        "[review] run_review_task started. task_id=%s, input_doc_ids=%s, knowhow_doc_ids=%s, batch_size=%s",
        task_id,
        input_doc_ids,
        knowhow_doc_ids,
        batch_size,
        )

        try:
            
            await self.repository.update_task_progress(
            task_id=task_id,
            status="running",
            )

            logger.info("[review] task status updated to running. task_id=%s", task_id)
            
            wrapper = LLMWrapper()
            llm = wrapper.get_llm(
                model_type=os.getenv("LLM_TYPE"),
                temperature=0,
            )
            
            graph = build_review_graph(
                llm=llm,
                repository=self.repository,
                meili_client=self.repository.get_meili_client(),
                meili_index_name=self.repository.get_meili_index_name(),
            )

            await graph.ainvoke(
                {
                    "task_id": task_id,
                    "input_doc_ids": input_doc_ids,
                    "knowhow_doc_ids": knowhow_doc_ids,
                    "batch_size": batch_size,
                }
            )

        except Exception as e:
            # rollback後にfailedに更新
            logger.exception("[review] run_review_task failed. task_id=%s", task_id)

            await self.repository.rollback()
            
            await self.repository.update_task_status(
                task_id=task_id,
                status="failed",
                error_message=str(e),
            )
            return


    async def get_task(
        self,
        *,
        task_id: int,
    ):
        return await self.repository.get_task(task_id=task_id)

    async def list_results(
        self,
        *,
        task_id: int,
    ):
        return await self.repository.list_results(task_id=task_id)
    
    async def list_review_documents(
        self,
        document_role: str,
    ):
        if document_role not in ["review_rule", "review_input"]:
            raise ValueError("document_role must be review_rule or review_input")

        documents = await self.repository.list_documents_by_role(document_role)

        return [
            {
                "doc_id": str(
                    getattr(doc, "doc_id", None)
                    or getattr(doc, "document_id", None)
                    or getattr(doc, "id", "")
                ),
                "file_name": (
                    getattr(doc, "file_name", None)
                    or getattr(doc, "filename", None)
                    or getattr(doc, "document_name", None)
                    or getattr(doc, "name", None)
                    or getattr(doc, "title", None)
                    or ""
                ),
                "document_role": getattr(doc, "document_role", document_role),
                "created_at": getattr(doc, "created_at", None),
                "updated_at": getattr(doc, "updated_at", None),
            }
            for doc in documents
        ]
        
    async def update_review_result_feedback(
        self,
        task_id: str,
        result_id: str,
        payload,
    ):
        review_result = await self.repository.update_result_feedback(
            task_id=task_id,
            result_id=result_id,
            human_status=payload.human_status,
            human_comment=payload.human_comment,
            corrected_finding=payload.corrected_finding,
            corrected_reason=payload.corrected_reason,
            corrected_suggestion=payload.corrected_suggestion,
        )

        if review_result is None:
            raise HTTPException(status_code=404, detail="Review result not found")

        return review_result
    
    
