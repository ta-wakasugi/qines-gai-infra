from dotenv import load_dotenv
from fastapi import Depends
from meilisearch_python_sdk import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from qines_gai_backend.logger_config import log_function_start_end
from qines_gai_backend.modules.ai.repositories import AIRepository
from qines_gai_backend.modules.artifacts.repositories import ArtifactRepository
from qines_gai_backend.modules.collections.repositories import CollectionRepository
from qines_gai_backend.modules.conversations.repositories import ConversationRepository
from qines_gai_backend.modules.conversion.repositories import ConversionRepository
from qines_gai_backend.modules.documents.repositories import DocumentRepository

from .data_connection import get_db_session, get_meili_client

load_dotenv("/app/.env")


@log_function_start_end
# リポジトリ依存性
async def get_conversation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ConversationRepository:
    return ConversationRepository(session)


@log_function_start_end
async def get_collection_repository(
    session: AsyncSession = Depends(get_db_session),
) -> CollectionRepository:
    return CollectionRepository(session)


@log_function_start_end
async def get_document_repository(
    session: AsyncSession = Depends(get_db_session),
    meili_client: AsyncClient = Depends(get_meili_client),
) -> DocumentRepository:
    return DocumentRepository(session, meili_client)


@log_function_start_end
async def get_ai_repository(
    session: AsyncSession = Depends(get_db_session),
    meili_client: AsyncClient = Depends(get_meili_client),
) -> AIRepository:
    return AIRepository(session, meili_client)


@log_function_start_end
async def get_artifact_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ArtifactRepository:
    return ArtifactRepository(session)


@log_function_start_end
async def get_conversion_repository(
    session: AsyncSession = Depends(get_db_session),
    meili_client: AsyncClient = Depends(get_meili_client),
) -> ConversionRepository:
    return ConversionRepository(session, meili_client)
