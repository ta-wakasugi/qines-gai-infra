from fastapi import APIRouter, Body, Depends, HTTPException, Path

from qines_gai_backend.config.dependencies.data_connection import User, get_current_user
from qines_gai_backend.config.dependencies.services import get_collection_service
from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.collections.models import (
    CollectionDetail,
    CreateCollectionRequest,
    GetCollectionsRequest,
    RetrieveCollectionsResponse,
    SharedCollection,
)
from qines_gai_backend.modules.collections.services import CollectionService
from qines_gai_backend.modules.conversations.models import ConversationBase
from qines_gai_backend.shared.exceptions import (
    BaseAppError,
    CollectionNotFoundError,
    NotAuthorizedCollectionError,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/api/collections",
    tags=["collections"],
    summary="A003:Create Collection",
    operation_id="A003",
    response_model=CollectionDetail,
)
@log_function_start_end
async def create_collection(
    body: CreateCollectionRequest,
    user: User = Depends(get_current_user),
    service: CollectionService = Depends(get_collection_service),
):
    """コレクションを新規作成する"""
    try:
        return await service.create_collection(user.user_id, body)
    except BaseAppError as e:
        logger.error(f"Collection creation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get(
    "/api/collections",
    tags=["collections"],
    summary="A004:Get Collections",
    operation_id="A004",
    response_model=RetrieveCollectionsResponse,
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
async def get_collections(
    body: GetCollectionsRequest = Depends(),
    user: User = Depends(get_current_user),
    service: CollectionService = Depends(get_collection_service),
):
    """ユーザーに紐づくコレクション一覧を取得する"""
    try:
        return await service.get_collections(user.user_id, body)
    except BaseAppError as e:
        logger.error(f"Collections retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@log_function_start_end
@router.get(
    "/api/collections/{public_collection_id}",
    tags=["collections"],
    summary="A005:Get Collection Detail",
    operation_id="A005",
    response_model=CollectionDetail,
    responses={
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
                            "value": {"detail": "Collection not found"}
                        }
                    },
                }
            },
        },
    },
)
async def get_collection(
    public_collection_id: str = Path(
        ..., description="公開コレクションID", examples=["V1StGXR8_Z5"]
    ),
    user: User = Depends(get_current_user),
    service: CollectionService = Depends(get_collection_service),
) -> CollectionDetail:
    """指定された公開コレクションIDのコレクション情報を取得する"""
    try:
        return await service.get_collection_detail(public_collection_id, user.user_id)
    except CollectionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotAuthorizedCollectionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except BaseAppError as e:
        logger.error(f"Collection detail retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.put(
    "/api/collections/{public_collection_id}",
    tags=["collections"],
    summary="A006:Update Collection",
    operation_id="A006",
    response_model=CollectionDetail,
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
                            "value": {"detail": "Not authorized to update this collection"}
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
                            "value": {"detail": "Collection not found"}
                        }
                    },
                }
            },
        },
    },
)
@log_function_start_end
async def update_collection(
    body: CreateCollectionRequest,
    public_collection_id: str = Path(
        ..., description="公開コレクションID", examples=["V1StGXR8_Z5"]
    ),
    user: User = Depends(get_current_user),
    service: CollectionService = Depends(get_collection_service),
):
    """指定された公開コレクションIDのコレクション情報を更新する"""
    try:
        return await service.update_collection(public_collection_id, user.user_id, body)
    except CollectionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotAuthorizedCollectionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except BaseAppError as e:
        logger.error(f"Collection update failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.delete(
    "/api/collections/{public_collection_id}",
    tags=["collections"],
    summary="A007:Delete Collection",
    operation_id="A007",
    status_code=204,
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
                            "value": {"detail": "Not authorized to delete this collection"}
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
                            "value": {"detail": "Collection not found"}
                        }
                    },
                }
            },
        },
    },
)
def delete_collection(
    public_collection_id: str = Path(
        ..., description="公開コレクションID", examples=["V1StGXR8_Z5"]
    ),
):
    """コレクションを削除する（未実装）"""
    return


@router.get(
    "/api/collections/{public_collection_id}/conversations",
    tags=["collections"],
    summary="A008:Get Conversations",
    operation_id="A008",
    response_model=list[ConversationBase],
    responses={
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
                            "value": {"detail": "Collection not found"}
                        }
                    },
                }
            },
        },
    },
)
@log_function_start_end
async def get_conversations(
    public_collection_id: str = Path(
        ..., description="公開コレクションID", examples=["V1StGXR8_Z5"]
    ),
    user: User = Depends(get_current_user),
    service: CollectionService = Depends(get_collection_service),
):
    """コレクションに紐づく会話履歴の一覧を取得する"""
    try:
        return await service.get_collection_conversations(
            public_collection_id, user.user_id
        )
    except CollectionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotAuthorizedCollectionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except BaseAppError as e:
        logger.error(f"Collection conversations retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post(
    "/api/collections/share",
    tags=["collections"],
    summary="A014:Share Collection",
    operation_id="A014",
    response_model=SharedCollection,
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
                        "insufficient_permission": {
                            "value": {"detail": "Insufficient Permission"}
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
                            "value": {"detail": "Collection not found"}
                        }
                    },
                }
            },
        },
    },
)
async def share_collection(
    public_collection_id: str = Body(
        ..., description="共有したいコレクションのID", examples=["V1StGXR8_Z5"], embed=True
    ),
):
    """コレクションを共有する（未実装）"""
    return
