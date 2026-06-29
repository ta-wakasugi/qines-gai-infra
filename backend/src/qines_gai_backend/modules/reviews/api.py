from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Path, Response
from uuid import UUID
from mypy_boto3_s3 import S3Client

from qines_gai_backend.config.dependencies.services import get_review_service
from qines_gai_backend.config.dependencies.data_connection import get_s3_client
from qines_gai_backend.config.dependencies.services import get_document_service
from qines_gai_backend.modules.documents.services import DocumentService

from qines_gai_backend.shared.exceptions import (
    BaseAppError,
    DocumentNotAuthorizedError,
    DocumentNotFoundError,
)

from qines_gai_backend.modules.reviews.models import (
    CreateReviewRequest,
    CreateReviewResponse,
    ReviewResultResponse,
    ReviewTaskResponse,
    ReviewDocumentResponse,
    ReviewResultFeedbackUpdate,
)
from qines_gai_backend.modules.reviews.services import ReviewService

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
)


@router.post("", response_model=CreateReviewResponse)
async def create_review(
    request: CreateReviewRequest,
    background_tasks: BackgroundTasks,
    service: ReviewService = Depends(get_review_service),
):
    """
    レビュータスクを作成し、バックグラウンドでAIレビューを開始する。
    """

    task = await service.create_review_task(
        input_doc_ids=request.input_doc_ids,
        knowhow_doc_ids=request.knowhow_doc_ids,
    )

    background_tasks.add_task(
        service.run_review_task,
        task_id=task.id,
        input_doc_ids=request.input_doc_ids,
        knowhow_doc_ids=request.knowhow_doc_ids,
        batch_size=request.batch_size,
    )

    return CreateReviewResponse(
        task_id=task.id,
        status=task.status,
    )

@router.get("/documents", response_model=list[ReviewDocumentResponse])
async def list_review_documents(
    document_role: str = Query(..., pattern="^(review_rule|review_input)$"),
    service: ReviewService = Depends(get_review_service),
):
    return await service.list_review_documents(document_role)

@router.get("/{task_id}", response_model=ReviewTaskResponse)
async def get_review_task(
    task_id: UUID,
    service: ReviewService = Depends(get_review_service),
):
    """
    レビュー進捗を取得する。
    """

    task = await service.get_task(task_id=task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Review task not found")

    progress = 0.0
    if task.total_rules > 0:
        progress = task.completed_rules / task.total_rules

    return ReviewTaskResponse(
        task_id=task.id,
        status=task.status,
        total_rules=task.total_rules,
        completed_rules=task.completed_rules,
        progress=progress,
        summary=task.summary,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("/{task_id}/results", response_model=list[ReviewResultResponse])
async def list_review_results(
    task_id: UUID,
    service: ReviewService = Depends(get_review_service),
):
    """
    レビュー指摘結果一覧を取得する。
    """

    task = await service.get_task(task_id=task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Review task not found")

    results = await service.list_results(task_id=task_id)

    return [
        ReviewResultResponse(
            id=result.id,
            task_id=result.task_id,
            rule_id=result.rule_id,
            status=result.status,
            severity=result.severity,
            target=result.target,
            finding=result.finding,
            reason=result.reason,
            suggestion=result.suggestion,
            evidences=result.evidences,
            created_at=result.created_at,
        )
        for result in results
    ]
    

@router.patch("/{task_id}/results/{result_id}")
async def update_review_result_feedback(
    task_id: str,
    result_id: str,
    payload: ReviewResultFeedbackUpdate,
    service: ReviewService = Depends(get_review_service),
):
    return await service.update_review_result_feedback(
        task_id=task_id,
        result_id=result_id,
        payload=payload,
    )
    
@router.delete("/documents/{document_id}", status_code=204)
async def delete_review_document(
    document_id: str = Path(..., description="レビュー用ドキュメントID"),
    document_service: DocumentService = Depends(get_document_service),
    s3_client: S3Client = Depends(get_s3_client),
):
    try:
        await document_service.delete_review_document(
            document_id=document_id,
            s3_client=s3_client,
        )
        return Response(status_code=204)

    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DocumentNotAuthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except BaseAppError as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
@router.get("/{task_id}/case-results")
async def get_review_case_results(
    task_id: str,
    service: ReviewService = Depends(get_review_service),
):
    return await service.get_review_case_results(task_id)