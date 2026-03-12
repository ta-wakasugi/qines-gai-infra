from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Path,
    Query,
    Response,
    UploadFile,
)
from meilisearch_python_sdk.errors import MeilisearchApiError
from mypy_boto3_s3 import S3Client
from typing_extensions import Literal

from qines_gai_backend.config.dependencies.data_connection import (
    User,
    get_current_user,
    get_s3_client,
)
from qines_gai_backend.config.dependencies.services import get_document_service
from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.documents.models import (
    DocumentBase,
    SearchDocumentsRequest,
    SearchDocumentsResponse,
    UploadDocumentRequest,
)
from qines_gai_backend.modules.documents.services import DocumentService
from qines_gai_backend.shared.exceptions import (
    BaseAppError,
    DocumentNotAuthorizedError,
    DocumentNotFoundError,
    DocumentValidationError,
)

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/api/documents/search",
    tags=["documents"],
    summary="A002:Search Document",
    operation_id="A002",
    response_model=SearchDocumentsResponse,
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
                        "invalid_query": {
                            "value": {"detail": "Invalid query parameter value"}
                        }
                    },
                }
            },
        },
    },
)
@log_function_start_end
async def search_document(
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
    q: str | None = Query(None, description="検索クエリ", examples=["CAN driver"]),
    hits_per_page: int | None = Query(
        default=7, description="1ページに含める検索結果の数", examples=[7]
    ),
    page: int | None = Query(default=1, description="取得したいページ番号", examples=[1]),
    uploader: list[Literal["user", "admin"]] | None = Query(
        ["user", "admin"],
        description="ドキュメントのアップロード者(['user']または['admin']または['user', 'admin']のリスト)",
        examples=[["admin"]],
        alias="uploader[]",
    ),
    genre: str | None = Query(
        None, description="AUTOSARドキュメントのワーキンググループ", examples=["SWS,EXP"]
    ),
    release: str | None = Query(
        None,
        description="AUTOSARドキュメントのリリースバージョン",
        examples=["R4-2-2"],
    ),
):
    """
    指定したクエリをもとにドキュメントを検索します。

    Args:
        user(User): 認証済みユーザー情報
        service(DocumentService): ドキュメントサービス
        q(str): 検索クエリ
        hits_per_page(int): 1ページに含めるデータの最大数(デフォルト:7)
        page(int): データを取得したいページ番号(デフォルト:1)
        uploader(list[Literal['user', 'admin']]): ドキュメントのアップロード者('user'または'admin')
        genre(str | None): AUTOSARドキュメントのワーキンググループ
        release(str | None): AUTOSARドキュメントのリリースバージョン

    Returns:
        SearchDocumentsResponse: 検索結果をマッピングしたレスポンス。

    Raises:
        HTTPException(400): クエリパラメータ関係のエラーが発生した場合。
        HTTPException(500): サーバーエラーが発生した場合。
    """
    try:
        request = SearchDocumentsRequest(
            q=q,
            hits_per_page=hits_per_page,
            page=page,
            uploader=uploader,
            genre=genre,
            release=release,
        )

        return await service.search_documents(user.user_id, request)

    except MeilisearchApiError as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid query parameter value")
    except BaseAppError as e:
        logger.error(f"Document search failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post(
    "/api/documents/upload",
    tags=["documents"],
    summary="A016:Upload Document",
    operation_id="A016",
    response_model=DocumentBase,
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
                        "invalid_file": {
                            "value": {"detail": "Invalid file request"}
                        }
                    },
                }
            },
        },
    },
)
@log_function_start_end
async def upload_file(
    file: UploadFile = File(..., description="ユーザーがアップロードしたファイル"),
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
    s3_client: S3Client = Depends(get_s3_client),
):
    """ファイルアップロードエンドポイント

    Args:
        file (UploadFile): アップロードされたファイル
        user (User): 現在のユーザー
        service (DocumentService): ドキュメントサービス
        s3_client (S3Client): S3クライアント

    Returns:
        DocumentBase: アップロードされたドキュメント情報

    Raises:
        HTTPException: 処理失敗時のエラー
    """
    try:
        request = UploadDocumentRequest()  # デフォルトで"others"

        return await service.upload_document(file, user.user_id, request, s3_client)

    except DocumentValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BaseAppError as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error occurred")


@router.delete(
    "/api/documents/{document_id}",
    tags=["documents"],
    summary="A017:Delete Document",
    operation_id="A017",
    responses={
        403: {
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
                        "not_authorized": {
                            "value": {"detail": "Not authorized to delete this document"}
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
                            "value": {"detail": "Document not found"}
                        }
                    },
                }
            },
        },
    },
)
@log_function_start_end
async def delete_document(
    document_id: str = Path(
        ...,
        description="ドキュメントID",
        examples=["260ea4dd-36a7-401f-b2a1-d6a28d97f140"],
    ),
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
    s3_client: S3Client = Depends(get_s3_client),
):
    """指定されたドキュメントを削除する

    Meilisearchのドキュメント削除に失敗した場合は検索APIやエージェントツールで使用
    されてしまうため以下の順番で削除処理を行い、途中で失敗した場合は後続処理へ進まない
        1. Meilisearch
        2. DB
        3. S3

    Args:
        document_id: 削除対象のドキュメントのID
        user: リクエストしたユーザー情報
        service: ドキュメントサービス
        s3_client: AWS S3のクライアント

    Returns:
        Response: ステータスコード204で削除が成功したことを示す

    Raises:
        HTTPException:
            - 403: ユーザーに削除する権限がないとき
            - 404: 指定されたドキュメントが存在しないとき
    """
    try:
        await service.delete_document(document_id, user.user_id, s3_client)
        return Response(status_code=204)

    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DocumentNotAuthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except BaseAppError as e:
        logger.error(f"Document deletion failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
