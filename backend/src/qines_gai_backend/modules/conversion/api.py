"""Update module API layer

成果物の更新処理に関するAPIエンドポイントを提供します。
AIによって生成された成果物をドキュメントとして登録・更新する機能を含みます。
"""

from fastapi import APIRouter, Body, Depends, HTTPException
from mypy_boto3_s3 import S3Client

from qines_gai_backend.config.dependencies.data_connection import (
    User,
    get_current_user,
    get_s3_client,
)
from qines_gai_backend.config.dependencies.services import get_conversion_service
from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.conversion.models import (
    AddDocumentRequest,
    AddDocumentResponse,
    UpdateDocumentRequest,
    UpdateDocumentResponse,
)
from qines_gai_backend.modules.conversion.services import ConversionService
from qines_gai_backend.shared.exceptions import (
    ArtifactNotFoundError,
    BaseAppError,
    DocumentUpdateError,
    DocumentUpdateValidationError,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/api/documents/from-artifact",
    tags=["conversion"],
    summary="A021:add document",
    operation_id="A021",
    response_model=AddDocumentResponse,
    responses={
        400: {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "description": "Error detail message",
                            }
                        },
                        "required": ["detail"],
                    },
                    "examples": {
                        "invalid_request": {
                            "value": {"detail": "Invalid request parameters"}
                        }
                    },
                }
            },
        },
        404: {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "description": "Error detail message",
                            }
                        },
                        "required": ["detail"],
                    },
                    "examples": {
                        "not_found": {
                            "value": {"detail": "Artifact not found"}
                        }
                    },
                }
            },
        },
        500: {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "description": "Error detail message",
                            }
                        },
                        "required": ["detail"],
                    },
                    "examples": {
                        "internal_error": {
                            "value": {"detail": "Internal Server Error"}
                        }
                    },
                }
            },
        },
    },
)
@log_function_start_end
async def add_document(
    request: AddDocumentRequest = Body(
        ..., description="成果物新規追加リクエストデータ"
    ),
    user: User = Depends(get_current_user),
    conversion_service: ConversionService = Depends(get_conversion_service),
    s3_client: S3Client = Depends(get_s3_client),
):
    """成果物をもとにドキュメントを新規追加する。

    指定されたアーティファクトIDとバージョンに基づいて成果物を取得し、
    新しいドキュメントIDを生成してドキュメントとして登録します。

    処理フロー:
    1. 成果物情報を取得
    2. 成果物IDを新しいドキュメントIDに変更
    3. S3に成果物を保存
    4. 成果物を新しいドキュメントとして登録（DB + MeilSearch）


    Args:
        request (AddDocumentRequest): 成果物新規追加リクエストデータ
        user (User): 認証されたユーザー情報
        conversion_service (ConversionService): ドキュメント操作サービス
        s3_client (S3Client): S3クライアント

    Returns:
        AddDocumentResponse: 新規追加処理の結果（成功/失敗、ドキュメントID、タイトル等）

    Raises:
        HTTPException: 以下の場合にHTTPExceptionが発生します：
            - 400: リクエストパラメータが不正な場合
            - 404: 指定された成果物が存在しない場合
            - 500: 内部サーバーエラーが発生した場合
    """
    try:
        # 成果物をもとにドキュメントを新規追加処理を実行
        result = await conversion_service.add_document_from_artifact(
            public_collection_id=request.public_collection_id,
            artifact_id=request.artifact_id,
            version=request.version,
            user_id=user.user_id,
            s3_client=s3_client,
        )

        logger.info(
            f"Add successfully. Document ID: {result['document_id']}, Title: {result['title']}"
        )

        return AddDocumentResponse(
            success=True,
            message="Document added successfully",
            document_id=result["document_id"],
            title=result["title"],
        )

    except DocumentUpdateValidationError as e:
        logger.warning(f"Validation error in add_document: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ArtifactNotFoundError as e:
        logger.warning(f"Artifact not found in add_document: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except DocumentUpdateError as e:
        logger.error(f"Document add failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except BaseAppError as e:
        logger.error(f"Application error in add_document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process add request")
    except Exception as e:
        logger.error(f"Unexpected error in add_document: {str(e)}", stack_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.patch(
    "/api/documents/from-artifact",
    tags=["conversion"],
    summary="A022:update document",
    operation_id="A022",
    response_model=UpdateDocumentResponse,
    responses={
        400: {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "description": "Error detail message",
                            }
                        },
                        "required": ["detail"],
                    },
                    "examples": {
                        "invalid_request": {
                            "value": {"detail": "Invalid request parameters"}
                        }
                    },
                }
            },
        },
        404: {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "description": "Error detail message",
                            }
                        },
                        "required": ["detail"],
                    },
                    "examples": {
                        "not_found": {
                            "value": {"detail": "Artifact not found"}
                        }
                    },
                }
            },
        },
        500: {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "description": "Error detail message",
                            }
                        },
                        "required": ["detail"],
                    },
                    "examples": {
                        "internal_error": {
                            "value": {"detail": "Internal Server Error"}
                        }
                    },
                }
            },
        },
    },
)
@log_function_start_end
async def update_document(
    request: UpdateDocumentRequest = Body(
        ..., description="成果物更新リクエストデータ"
    ),
    user: User = Depends(get_current_user),
    update_service: ConversionService = Depends(get_conversion_service),
    s3_client: S3Client = Depends(get_s3_client),
):
    """成果物をもとにドキュメントを上書き保存する。

    指定されたアーティファクトIDとバージョンに基づいて成果物と関連ドキュメントのIDを取得し、
    既存のドキュメントを削除後、新しいドキュメントとして登録します。
    既存ドキュメントがコレクションに含まれている場合、コレクション内の参照も更新されます。

    処理フロー:
    1. 成果物情報を取得
    2. document_idで既存ドキュメントを検索
    3. S3に成果物を保存
    4. 成果物を新しいドキュメントとして登録（DB + MeilSearch）


    Args:
        request (UpdateDocumentRequest): 成果物更新リクエストデータ
        user (User): 認証されたユーザー情報
        update_service (UpdateService): 更新サービス
        s3_client (S3Client): S3クライアント

    Returns:
        UpdateDocumentResponse: 更新処理の結果（成功/失敗、ドキュメントID、タイトル等）

    Raises:
        HTTPException: 以下の場合にHTTPExceptionが発生します：
            - 400: リクエストパラメータが不正な場合
            - 404: 指定された成果物が存在しない場合
            - 500: 内部サーバーエラーが発生した場合
    """
    try:
        # 成果物をもとにドキュメントを更新処理を実行
        result = await update_service.update_document_from_artifact(
            public_collection_id=request.public_collection_id,
            artifact_id=request.artifact_id,
            version=request.version,
            user_id=user.user_id,
            s3_client=s3_client,
        )

        logger.info(
            f"Update successfully. Document ID: {result['document_id']}, Title: {result['title']}"
        )

        return UpdateDocumentResponse(
            success=True,
            message="Document updated successfully",
            document_id=result["document_id"],
            title=result["title"],
        )

    except DocumentUpdateValidationError as e:
        logger.warning(f"Validation error in update_artifact: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ArtifactNotFoundError as e:
        logger.warning(f"Artifact not found in update_artifact: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except DocumentUpdateError as e:
        logger.error(f"Document update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except BaseAppError as e:
        logger.error(f"Application error in update_artifact: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process update request")
    except Exception as e:
        logger.error(f"Unexpected error in update_artifact: {str(e)}", stack_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
