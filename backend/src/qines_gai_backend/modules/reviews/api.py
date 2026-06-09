from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from uuid import UUID

from qines_gai_backend.config.dependencies.services import get_review_service
from qines_gai_backend.modules.reviews.models import (
    CreateReviewRequest,
    CreateReviewResponse,
    ReviewResultResponse,
    ReviewTaskResponse,
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