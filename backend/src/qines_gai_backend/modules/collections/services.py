from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.collections.models import (
    CollectionBase,
    CollectionDetail,
    CreateCollectionRequest,
    GetCollectionsRequest,
    RetrieveCollectionsResponse,
)
from qines_gai_backend.modules.collections.repositories import CollectionRepository
from qines_gai_backend.modules.conversations.models import ConversationBase
from qines_gai_backend.shared.exceptions import (
    BaseAppError,
    CollectionNotFoundError,
    NotAuthorizedCollectionError,
)

logger = get_logger(__name__)


class CollectionService:
    """コレクション関連のビジネスロジック層"""

    def __init__(self, repository: CollectionRepository):
        """CollectionServiceを初期化する。

        Args:
            repository (CollectionRepository): コレクションデータアクセス用リポジトリ
        """
        self.repository = repository

    @log_function_start_end
    async def create_collection(
        self, user_id: str, request: CreateCollectionRequest
    ) -> CollectionDetail:
        """コレクションを新規作成する"""
        try:
            collection = await self.repository.create_collection(
                user_id=user_id, name=request.name, document_uuids=request.document_ids
            )

            # 作成されたコレクションの詳細情報を取得
            (
                collection,
                collection_documents,
            ) = await self.repository.get_collection_with_documents(
                collection.public_collection_id
            )

            # commit前にPydanticモデルに変換（commit後はdetached状態になるため）
            result = CollectionDetail.from_db(collection, collection_documents)

            await self.repository.commit()
            return result

        except Exception as e:
            await self.repository.rollback()
            logger.error(f"Error creating collection: {e}")
            raise BaseAppError("Failed to create collection")

    @log_function_start_end
    async def get_collections(
        self, user_id: str, request: GetCollectionsRequest
    ) -> RetrieveCollectionsResponse:
        """ユーザーに紐づくコレクション一覧を取得する"""
        try:
            collections, total = await self.repository.get_collections_by_user(
                user_id=user_id, offset=request.offset, limit=request.limit
            )

            collection_bases = [
                CollectionBase.from_db(collection) for collection in collections
            ]

            return RetrieveCollectionsResponse(
                total=total,
                offset=request.offset,
                limit=request.limit,
                collections=collection_bases,
            )

        except Exception as e:
            logger.error(f"Error retrieving collections: {e}")
            raise BaseAppError("Failed to retrieve collections")

    @log_function_start_end
    async def get_collection_detail(
        self, public_collection_id: str, user_id: str
    ) -> CollectionDetail:
        """指定された公開コレクションIDのコレクション詳細情報を取得する"""
        try:
            (
                collection,
                collection_documents,
            ) = await self.repository.get_collection_with_documents(
                public_collection_id, user_id
            )

            return CollectionDetail.from_db(collection, collection_documents)

        except (CollectionNotFoundError, NotAuthorizedCollectionError):
            raise
        except Exception as e:
            logger.error(f"Error retrieving collection detail: {e}")
            raise BaseAppError("Failed to retrieve collection detail")

    @log_function_start_end
    async def update_collection(
        self,
        public_collection_id: str,
        user_id: str,
        request: CreateCollectionRequest,
    ) -> CollectionDetail:
        """指定された公開コレクションIDのコレクション情報を更新する"""
        try:
            # 権限チェックを含むコレクション取得
            try:
                collection = await self.repository.get_collection_by_public_id(
                    public_collection_id, user_id
                )
            except NotAuthorizedCollectionError:
                raise NotAuthorizedCollectionError(
                    "Not authorized to update this collection"
                )

            # コレクションを更新
            await self.repository.update_collection(
                collection_id=collection.collection_id,
                name=request.name,
                document_uuids=request.document_ids,
            )

            # 更新されたコレクションの詳細情報を取得
            (
                collection,
                collection_documents,
            ) = await self.repository.get_collection_with_documents(
                public_collection_id
            )

            # commit前にPydanticモデルに変換（commit後はdetached状態になるため）
            result = CollectionDetail.from_db(collection, collection_documents)

            await self.repository.commit()
            return result

        except (CollectionNotFoundError, NotAuthorizedCollectionError):
            await self.repository.rollback()
            raise
        except Exception as e:
            await self.repository.rollback()
            logger.error(f"Error updating collection: {e}")
            raise BaseAppError("Failed to update collection")

    @log_function_start_end
    async def get_collection_conversations(
        self, public_collection_id: str, user_id: str
    ) -> list[ConversationBase]:
        """コレクションに紐づく会話履歴の一覧を取得する"""
        try:
            # 権限チェックを含むコレクション取得
            collection = await self.repository.get_collection_by_public_id(
                public_collection_id, user_id
            )

            conversations = await self.repository.get_conversations_by_collection(
                collection.collection_id, user_id
            )

            return [
                ConversationBase(
                    public_conversation_id=conversation.public_conversation_id,
                    title=conversation.title,
                )
                for conversation in conversations
            ]

        except (CollectionNotFoundError, NotAuthorizedCollectionError):
            raise
        except Exception as e:
            logger.error(f"Error retrieving collection conversations: {e}")
            raise BaseAppError("Failed to retrieve collection conversations")
