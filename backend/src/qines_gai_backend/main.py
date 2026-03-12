from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from qines_gai_backend.config.dependencies.data_connection import get_connection_manager
from qines_gai_backend.logger_config import get_logger
from qines_gai_backend.modules.ai.api import router as ai_service_router
from qines_gai_backend.modules.artifacts.api import router as artifacts_service_router
from qines_gai_backend.modules.collections.api import (
    router as collections_service_router,
)
from qines_gai_backend.modules.conversations.api import (
    router as conversation_service_router,
)
from qines_gai_backend.modules.conversion.api import router as conversion_service_router
from qines_gai_backend.modules.documents.api import router as documents_service_router

load_dotenv("/app/.env")
logger = get_logger(__name__)


def create_app():
    """FastAPIオブジェクトを作成する関数

    この関数では、外部リソースとの接続状態を確認しAPIサーバーが機能を提供できるかを確認した上で、
    FastAPIクラスのオブジェクトを作成します。
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator:
        try:
            connection_manager = get_connection_manager()
            await connection_manager.connect_all()
            yield
        finally:
            try:
                await connection_manager.disconnect_all()
            except Exception as e:
                logger.error(
                    f"アプリケーションのシャットダウン中にエラーが発生しました: {e}"
                )

    tags_metadata = [
        {
            "name": "documents",
            "description": "Operations with documents.",
        },
        {
            "name": "collections",
            "description": "Operations with collections",
        },
        {
            "name": "ai",
            "description": "Operations with LLM.",
        },
        {
            "name": "conversations",
            "description": "Operations with conversations.",
        },
        {
            "name": "conversion",
            "description": "Operations with conversion.",
        },
    ]

    app = FastAPI(
        openapi_tags=tags_metadata,
        lifespan=lifespan,
        responses={
            401: {
                "description": "Unauthorized",
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
                            "missing_token": {
                                "summary": "Missing token",
                                "value": {"detail": "Authorization header missing"},
                            },
                            "invalid_or_expired_token": {
                                "summary": "Invalid or expired token",
                                "value": {"detail": "Invalid or expired token"},
                            },
                        },
                    }
                },
            },
            500: {
                "description": "Internal Server Error",
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
                        "example": {"detail": "Internal Server Error"},
                    }
                },
            },
        },
    )
    return app


app = create_app()
app.include_router(documents_service_router)
app.include_router(collections_service_router)
app.include_router(ai_service_router)
app.include_router(conversation_service_router)
app.include_router(artifacts_service_router)
app.include_router(conversion_service_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
