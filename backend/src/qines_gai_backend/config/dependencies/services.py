from dotenv import load_dotenv
from fastapi import Depends

from qines_gai_backend.logger_config import log_function_start_end
from qines_gai_backend.modules.ai.repositories import AIRepository
from qines_gai_backend.modules.ai.services import AIService
from qines_gai_backend.modules.artifacts.repositories import ArtifactRepository
from qines_gai_backend.modules.artifacts.services import ArtifactService
from qines_gai_backend.modules.collections.repositories import CollectionRepository
from qines_gai_backend.modules.collections.services import CollectionService
from qines_gai_backend.modules.conversations.repositories import ConversationRepository
from qines_gai_backend.modules.conversations.services import ConversationService
from qines_gai_backend.modules.conversion.repositories import ConversionRepository
from qines_gai_backend.modules.conversion.services import ConversionService
from qines_gai_backend.modules.documents.repositories import DocumentRepository
from qines_gai_backend.modules.documents.services import DocumentService

from .repositories import (
    get_ai_repository,
    get_artifact_repository,
    get_collection_repository,
    get_conversation_repository,
    get_conversion_repository,
    get_document_repository,
)

load_dotenv("/app/.env")


@log_function_start_end
async def get_conversation_service(
    repository: ConversationRepository = Depends(get_conversation_repository),
) -> ConversationService:
    return ConversationService(repository)


@log_function_start_end
async def get_collection_service(
    repository: CollectionRepository = Depends(get_collection_repository),
) -> CollectionService:
    return CollectionService(repository)


@log_function_start_end
async def get_document_service(
    repository: DocumentRepository = Depends(get_document_repository),
) -> DocumentService:
    return DocumentService(repository)


@log_function_start_end
async def get_ai_service(
    repository: AIRepository = Depends(get_ai_repository),
) -> AIService:
    return AIService(repository)


@log_function_start_end
async def get_artifact_service(
    repository: ArtifactRepository = Depends(get_artifact_repository),
) -> ArtifactService:
    return ArtifactService(repository)


@log_function_start_end
async def get_conversion_service(
    repository: ConversionRepository = Depends(get_conversion_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
    artifact_repo: ArtifactRepository = Depends(get_artifact_repository),
) -> ConversionService:
    return ConversionService(repository, document_repo, artifact_repo)
