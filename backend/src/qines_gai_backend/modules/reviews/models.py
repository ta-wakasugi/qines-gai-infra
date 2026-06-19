from datetime import datetime
from typing import Any, Optional,Literal
from uuid import UUID

from pydantic import BaseModel, Field

class CreateReviewRequest(BaseModel):
    input_doc_ids: list[str] = Field(
        description="レビュー対象となるドキュメントID一覧"
    )
    knowhow_doc_ids: list[str] = Field(
        description="レビューに使用するノウハウMarkdownドキュメントID一覧"
    )
    batch_size: int = Field(
        default=5,
        ge=1,
        le=10,
        description="AIに一度に渡すノウハウルール数",
    )
    
class CreateReviewResponse(BaseModel):
    task_id: UUID
    status: str


class ReviewTaskResponse(BaseModel):
    task_id: UUID
    status: str
    total_rules: int
    completed_rules: int
    progress: float
    summary: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class ReviewEvidenceResponse(BaseModel):
    document_id: str | None = None
    chunk_id: str | None = None
    location: str | None = None
    quote: str


class ReviewResultResponse(BaseModel):
    id: UUID
    task_id: UUID
    rule_id: str
    status: Literal["ng", "unknown"]
    severity: Literal["low", "medium", "high"]
    target: str | None = None
    finding: str
    reason: str
    suggestion: str
    evidences: list[dict[str, Any]]
    created_at: datetime
    human_status: Optional[str] = None
    human_comment: Optional[str] = None
    corrected_finding: Optional[str] = None
    corrected_reason: Optional[str] = None
    corrected_suggestion: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    
    
class ReviewDocumentResponse(BaseModel):
    doc_id: str
    file_name: Optional[str] = None
    document_role: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
class ReviewResultFeedbackUpdate(BaseModel):
    human_status: Optional[
        Literal[
            "correct",
            "false_positive",
            "pending",
            "fixed",
            "needs_knowhow_update",
        ]
    ] = None
    human_comment: Optional[str] = None
    corrected_finding: Optional[str] = None
    corrected_reason: Optional[str] = None
    corrected_suggestion: Optional[str] = None
    
