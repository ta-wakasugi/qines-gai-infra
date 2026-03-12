from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from qines_gai_backend.config.dependencies.data_connection import User, get_current_user
from qines_gai_backend.config.dependencies.services import get_ai_service
from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.ai.models import (
    ChatCompletionsRequest,
    ChatRequestBase,
    StreamChat,
    TranslatedText,
    TranslateTextRequest,
)
from qines_gai_backend.modules.ai.services import AIService
from qines_gai_backend.modules.collections.models import CollectionDetail
from qines_gai_backend.shared.exceptions import (
    BaseAppError,
    CollectionCreationError,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/api/ai/translate",
    tags=["ai"],
    summary="A011:Translate",
    operation_id="A011",
    response_model=TranslatedText,
    deprecated=True,
)
def translate_text(body: TranslateTextRequest):
    """テキスト翻訳エンドポイント（非推奨）

    Args:
        body (TranslateTextRequest): 翻訳リクエストボディ

    Returns:
        TranslatedText: 翻訳結果（現在は未実装）

    Note:
        このエンドポイントは非推奨です。
    """
    return TranslatedText(result="")


@router.post(
    "/api/ai/chat/start",
    tags=["ai"],
    summary="A012:Start Chat",
    operation_id="A012",
    response_model=CollectionDetail,
)
@log_function_start_end
async def create_initial_collection(
    body: ChatRequestBase,
    user: User = Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
):
    """ユーザのリクエストに応じて初期コレクションを作成する

    ユーザーのメッセージに基づいて、関連するドキュメントを検索し、
    それらのドキュメントを含む新しいコレクションを作成します。

    Args:
        body (ChatRequestBase): リクエストボディ。メッセージデータが含まれる
        user (User): 認証済みユーザー情報
        service (AIService): AIサービス

    Returns:
        CollectionDetail: 作成されたコレクションの詳細情報

    Raises:
        HTTPException: 以下の場合にHTTPExceptionが発生します：
            - 500: コレクション作成に失敗した場合
            - 500: 内部サーバーエラーが発生した場合
    """
    try:
        return await service.create_initial_collection(user.user_id, body)

    except CollectionCreationError as e:
        logger.error(f"Collection creation failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create initial collection"
        )
    except BaseAppError as e:
        logger.error(f"AI service error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post(
    "/api/ai/chat/completions",
    tags=["ai"],
    summary="A013:Chat Completions",
    operation_id="A013",
    response_model=StreamChat,
    responses={
        200: {
            "content": {
                "text/event-stream": {
                    "schema": {"$ref": "#/components/schemas/StreamChat"}
                }
            },
        },
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
                            "value": {"detail": "Not authorized to use this collection"}
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
async def stream_chat(
    body: ChatCompletionsRequest,
    user: User = Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
):
    """ユーザーのリクエストに応じたチャットをストリーミングで返す

    指定されたコレクションと会話履歴を基に、AIエージェントが生成した
    レスポンスをServer-Sent Eventsでストリーミング配信します。
    新規の場合は会話を作成し、既存の場合は会話を継続します。

    Args:
        body (ChatCompletionsRequest): チャットのリクエスト
        user (User): 認証済みユーザー情報
        service (AIService): AIサービスインスタンス

    Returns:
        StreamingResponse: 以下の情報をJSONパース可能な文字列としてストリームします：
            - Message: メッセージオブジェクト
            - Artifact: アーティファクトオブジェクト
            - public_conversation_id: 会話ID文字列

    Raises:
        HTTPException: 以下の場合にHTTPExceptionが発生します：
            - 404: 指定されたコレクションが存在しない場合
            - 404: 指定された会話履歴が存在しない場合
            - 403: ユーザーがコレクションへのアクセス権限を持たない場合
            - 500: チャット処理に失敗した場合
            - 500: 内部サーバーエラーが発生した場合
    """
    # 事前バリデーション
    await service.validate_stream_chat_request(user.user_id, body)
    try:
        return StreamingResponse(
            service.stream_chat(user.user_id, body),
            media_type="application/x-ndjson",
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
