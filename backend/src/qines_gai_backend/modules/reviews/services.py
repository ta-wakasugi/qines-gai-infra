import os
from qines_gai_backend.modules.ai.agents.review_agent import build_review_graph
from qines_gai_backend.modules.reviews.repositories import ReviewRepository

from qines_gai_backend.modules.ai.agents.review_agent_schema import (
    Evidence,
    ReviewBatchOutput,
    ReviewFinding,
)

import re
from typing import Any


from qines_gai_backend.modules.ai.agents.review_agent_search import (
    load_input_contexts_from_meili,
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
    
    
    
    @staticmethod
    def _dump_obj(obj: Any) -> dict:
        if isinstance(obj, dict):
            return obj

        if hasattr(obj, "model_dump"):
            return obj.model_dump()

        if hasattr(obj, "dict"):
            return obj.dict()

        return getattr(obj, "__dict__", {})

    @staticmethod
    def _get_obj_value(obj: Any, key: str) -> Any:
        data = ReviewService._dump_obj(obj)

        if key in data:
            return data.get(key)

        metadata = data.get("metadata")
        if isinstance(metadata, dict) and key in metadata:
            return metadata.get(key)

        return getattr(obj, key, None)

    @staticmethod
    def _get_metadata(obj: Any) -> dict:
        data = ReviewService._dump_obj(obj)

        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        # MarkdownHeaderTextSplitter の h1/h2 が top-level に保存されている場合も拾う
        for key in ["h1", "h2", "h3", "h4"]:
            if key in data and key not in metadata:
                metadata[key] = data.get(key)

        return metadata

    @staticmethod
    def _get_context_text(context: Any) -> str:
        data = ReviewService._dump_obj(context)

        # 実際の Meilisearch schema によって本文フィールド名が違う可能性があるため広めに拾う
        for key in [
            "contents",
            "content",
            "text",
            "page_content",
            "chunk_text",
            "body",
            "markdown",
            "value",
        ]:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value

        # metadata 側に本文が入っている場合も一応拾う
        metadata = data.get("metadata")
        if isinstance(metadata, dict):
            for key in [
                "contents",
                "content",
                "text",
                "page_content",
                "chunk_text",
                "body",
            ]:
                value = metadata.get(key)
                if isinstance(value, str) and value.strip():
                    return value

        return ""

    @staticmethod
    def _extract_case_title_from_text(text: str) -> str | None:
        # "# Case 1: MSG_ENGINE_STATUS" のような h1 だけを拾う
        match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()

        return None

    @staticmethod
    def _dump_review_result(result: Any) -> dict:
        data = ReviewService._dump_obj(result)

        return {
            "id": str(data.get("id")),
            "rule_id": data.get("rule_id"),
            "status": data.get("status"),
            "severity": data.get("severity"),
            "target": data.get("target"),
            "finding": data.get("finding"),
            "reason": data.get("reason"),
            "suggestion": data.get("suggestion"),
            "evidences": data.get("evidences") or [],
            "human_status": data.get("human_status"),
            "human_comment": data.get("human_comment"),
            "corrected_finding": data.get("corrected_finding"),
            "corrected_reason": data.get("corrected_reason"),
            "corrected_suggestion": data.get("corrected_suggestion"),
            "reviewed_at": data.get("reviewed_at"),
        }

    async def get_review_case_results(self, task_id: str) -> list[dict]:
        """
        レビュー対象データを case 単位で返す。
        指摘がない case も必ず返す。
        """

        task = await self.repository.get_task_by_id(task_id)

        if task is None:
            raise HTTPException(status_code=404, detail="Review task not found")

        input_doc_ids = task.input_doc_ids

        input_contexts = await load_input_contexts_from_meili(
            meili_client=self.repository.get_meili_client(),
            index_name=self.repository.get_meili_index_name(),
            input_doc_ids=input_doc_ids,
            document_role="review_input",
        )

        results = await self.repository.list_results_by_task_id(task_id)

        findings_by_chunk_id: dict[str, list[dict]] = {}

        for result in results:
            result_dict = self._dump_review_result(result)

            for evidence in result_dict.get("evidences", []):
                chunk_id = evidence.get("chunk_id")
                if not chunk_id:
                    continue

                findings_by_chunk_id.setdefault(str(chunk_id), []).append(result_dict)

        # chunk_num 順に並べる
        sorted_contexts = sorted(
            input_contexts,
            key=lambda context: (
                self._get_obj_value(context, "chunk_num")
                or self._get_metadata(context).get("chunk_num")
                or 0
            ),
        )

        cases_by_key: dict[str, dict] = {}
        current_case_title: str | None = None

        for index, context in enumerate(sorted_contexts):
            metadata = self._get_metadata(context)
            text = self._get_context_text(context)

            data = self._dump_obj(context)

            # 確認用ログ。動作確認後は消してOKです。
            logger.info(
                "[case-results] context index=%s keys=%s metadata=%s text_preview=%s",
                index,
                list(data.keys()),
                metadata,
                text[:120],
            )

            document_id = (
                self._get_obj_value(context, "document_id")
                or metadata.get("document_id")
                or self._get_obj_value(context, "doc_id")
                or metadata.get("doc_id")
            )

            chunk_id = (
                self._get_obj_value(context, "chunk_id")
                or metadata.get("chunk_id")
                or self._get_obj_value(context, "id")
            )

            chunk_num = (
                self._get_obj_value(context, "chunk_num")
                or metadata.get("chunk_num")
                or index
            )

            # h1 が取れれば、それを case title にする
            case_title = (
                metadata.get("h1")
                or self._get_obj_value(context, "h1")
                or self._extract_case_title_from_text(text)
            )

            # MarkdownHeaderTextSplitter の都合で h2 チャンクに h1 が入らない場合は、
            # 直前の h1 を引き継ぐ
            if case_title:
                current_case_title = str(case_title)

            if not current_case_title:
                current_case_title = f"Case {index + 1}"

            case_key = f"{document_id}:{current_case_title}"

            if case_key not in cases_by_key:
                cases_by_key[case_key] = {
                    "case_id": case_key,
                    "title": current_case_title,
                    "document_id": str(document_id) if document_id else None,
                    "chunk_ids": [],
                    "chunks": [],
                    "content": "",
                    "findings": [],
                }

            case = cases_by_key[case_key]

            if chunk_id:
                case["chunk_ids"].append(str(chunk_id))

            if text.strip():
                case["chunks"].append(
                    {
                        "chunk_id": str(chunk_id) if chunk_id else None,
                        "chunk_num": chunk_num,
                        "content": text,
                    }
                )

        case_results: list[dict] = []

        for case in cases_by_key.values():
            chunks = sorted(
                case["chunks"],
                key=lambda chunk: chunk.get("chunk_num") or 0,
            )

            case["content"] = "\n\n".join(
                chunk["content"] for chunk in chunks if chunk.get("content")
            )

            added_result_ids: set[str] = set()
            findings: list[dict] = []

            for chunk_id in case["chunk_ids"]:
                for finding in findings_by_chunk_id.get(chunk_id, []):
                    finding_id = finding.get("id")
                    if finding_id in added_result_ids:
                        continue

                    added_result_ids.add(finding_id)
                    findings.append(finding)

            case["findings"] = findings
            case.pop("chunks", None)

            case_results.append(case)

        return case_results