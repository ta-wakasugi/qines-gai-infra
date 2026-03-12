from fastapi import APIRouter, Body, Depends, HTTPException, Path

from qines_gai_backend.config.dependencies.data_connection import User, get_current_user
from qines_gai_backend.config.dependencies.services import get_conversation_service
from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.shared.exceptions import (
    ConversationNotFoundError,
    NotAuthorizedConversation,
)

from .models import ConversationDetail, SharedConversation
from .services import ConversationService

logger = get_logger(__name__)
router = APIRouter()

require_auth_err_response = {}


@router.get(
    "/api/conversations/{public_conversation_id}",
    tags=["conversations"],
    summary="A009:Get Conversation Detail",
    operation_id="A009",
    response_model=ConversationDetail,
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
                            "value": {"detail": "Conversation not found"}
                        }
                    },
                }
            },
        },
    },
)
@log_function_start_end
async def get_conversation(
    public_conversation_id: str = Path(
        ..., description="会話履歴の公開ID", examples=["Zf2k6A6R5h2"]
    ),
    user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    指定された会話履歴の公開IDの詳細を取得します。

    Args:
        public_conversation_id (str): 会話履歴の公開ID。パスパラメータから取得する。
        user (User): 認証済みユーザー情報。
        conversation_service (ConversationService): 会話サービス。

    Returns:
        conversation_detail (CoversationDetail): 会話履歴の詳細情報。

    Raises:
        HTTPException(403): ログインユーザーが会話履歴の所有者でない場合。
        HTTPException(404): 指定された会話履歴の公開IDが存在しない場合。
        HTTPException(500): 内部サーバーエラーが発生した場合。
    """

    try:
        return await conversation_service.get_conversation(
            public_conversation_id=public_conversation_id,
            user_id=user.user_id,
        )

    # 例外が発生した場合
    except NotAuthorizedConversation as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ConversationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Internal Server Error:{e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.delete(
    "/api/conversations/{public_conversation_id}",
    tags=["conversations"],
    summary="A010:Delete Conversation",
    operation_id="A010",
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
                            "value": {"detail": "Not authorized to delete this conversation"}
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
                            "value": {"detail": "Conversation not found"}
                        }
                    },
                }
            },
        },
    },
)
def delete_conversation(
    public_conversation_id: str = Path(
        ..., description="会話履歴の公開ID", examples=["Zf2k6A6R5h2"]
    ),
):
    """指定された公開会話履歴IDの会話履歴を論理削除する。

    Args:
        public_conversation_id (str): 削除したい会話履歴の公開ID

    Returns:
        ステータスコード204で空のレスポンス

    Raises:
        HTTPException(403): ログインユーザーが会話履歴の所有者でない場合
        HTTPException(404): 指定された会話履歴の公開IDが存在しない場合

    Note:
        現在未実装。将来の機能拡張用のプレースホルダー
    """
    return


@router.post(
    "/api/conversations/share",
    tags=["conversations"],
    summary="A015:Share Conversation",
    operation_id="A015",
    response_model=SharedConversation,
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
                            "value": {"detail": "Conversation not found"}
                        }
                    },
                }
            },
        },
    },
)
async def share_conversation(
    public_conversation_id: str = Body(
        ..., description="共有したい会話履歴のID", examples=["V1StGXR8_Z5"], embed=True
    ),
):
    """指定された公開会話履歴IDの会話履歴を共有可能な状態にし、共有URLを返す。

    Args:
        public_conversation_id (str): 共有したい会話履歴の公開ID

    Returns:
        SharedConversation: 共有用のURLや設定情報を含むレスポンス

    Raises:
        HTTPException(403): 権限不足の場合
        HTTPException(404): 指定された会話履歴が存在しない場合

    Note:
        現在未実装。将来の機能拡張用のプレースホルダー
    """
    return
