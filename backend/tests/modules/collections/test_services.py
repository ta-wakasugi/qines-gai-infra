import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from qines_gai_backend.modules.collections.models import (
    CollectionBase,
    CollectionDetail,
    CreateCollectionRequest,
    GetCollectionsRequest,
    RetrieveCollectionsResponse,
)
from qines_gai_backend.modules.collections.repositories import CollectionRepository
from qines_gai_backend.modules.collections.services import CollectionService
from qines_gai_backend.modules.conversations.models import ConversationBase
from qines_gai_backend.schemas.schema import T_Collection, T_Conversation
from qines_gai_backend.shared.exceptions import (
    BaseAppError,
    CollectionNotFoundError,
    NotAuthorizedCollectionError,
)


class TestCollectionService:
    """CollectionServiceのテストクラス"""

    @pytest.fixture
    def mock_repository(self):
        """CollectionRepositoryのモックを作成する"""
        return AsyncMock(spec=CollectionRepository)

    @pytest.fixture
    def service(self, mock_repository):
        """CollectionServiceのインスタンスを作成する"""
        return CollectionService(mock_repository)

    @pytest.fixture
    def sample_collection(self):
        """テスト用のコレクションを作成する"""
        collection = MagicMock(spec=T_Collection)
        collection.collection_id = uuid.uuid4()
        collection.public_collection_id = "test_id"
        collection.name = "Test Collection"
        collection.created_at = datetime(2023, 1, 1)
        collection.updated_at = datetime(2023, 1, 1)
        return collection

    @pytest.fixture
    def sample_conversation(self):
        """テスト用の会話履歴を作成する"""
        conversation = MagicMock(spec=T_Conversation)
        conversation.public_conversation_id = "conv_id"
        conversation.title = "Test Conversation"
        return conversation

    class TestInit:
        """__init__メソッドのテストクラス"""

        def test_init_success(self, mock_repository):
            """初期化が正常に行われることを確認する"""
            service = CollectionService(mock_repository)
            assert service.repository is mock_repository

    class TestCreateCollection:
        """create_collectionメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_create_collection_success(
            self, service, mock_repository, sample_collection
        ):
            """正常系：コレクション作成が成功することを確認する"""
            # Arrange
            user_id = "test_user"
            request = CreateCollectionRequest(
                name="Test Collection",
                document_ids=[str(uuid.uuid4()), str(uuid.uuid4())],
            )

            mock_repository.create_collection.return_value = sample_collection
            mock_repository.get_collection_with_documents.return_value = (
                sample_collection,
                [],
            )

            # Act
            with patch(
                "qines_gai_backend.modules.collections.models.CollectionDetail.from_db"
            ) as mock_from_db:
                expected_result = CollectionDetail(
                    public_collection_id="test_id",
                    name="Test Collection",
                    documents=[],
                    created_at=datetime(2023, 1, 1),
                    updated_at=datetime(2023, 1, 1),
                )
                mock_from_db.return_value = expected_result

                result = await service.create_collection(user_id, request)

                # Assert
                assert result == expected_result
                mock_repository.create_collection.assert_called_once()
                mock_repository.get_collection_with_documents.assert_called_once()
                mock_repository.commit.assert_called_once()

        @pytest.mark.asyncio
        async def test_create_collection_failure(self, service, mock_repository):
            """異常系：コレクション作成時の例外処理を確認する"""
            # Arrange
            user_id = "test_user"
            request = CreateCollectionRequest(name="Test Collection", document_ids=[])
            mock_repository.create_collection.side_effect = Exception("Database error")

            # Act & Assert
            with pytest.raises(BaseAppError) as exc_info:
                await service.create_collection(user_id, request)

            assert "Failed to create collection" in str(exc_info.value)
            mock_repository.rollback.assert_called_once()

    class TestGetCollections:
        """get_collectionsメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_collections_success(
            self, service, mock_repository, sample_collection
        ):
            """正常系：コレクション一覧取得が成功することを確認する"""
            # Arrange
            user_id = "test_user"
            request = GetCollectionsRequest(offset=0, limit=10)

            mock_repository.get_collections_by_user.return_value = (
                [sample_collection],
                1,
            )

            # Act
            with patch(
                "qines_gai_backend.modules.collections.models.CollectionBase.from_db"
            ) as mock_from_db:
                mock_collection_base = CollectionBase(
                    public_collection_id="test_id",
                    name="Test Collection",
                    created_at=datetime(2023, 1, 1),
                    updated_at=datetime(2023, 1, 1),
                )
                mock_from_db.return_value = mock_collection_base

                result = await service.get_collections(user_id, request)

                # Assert
                assert isinstance(result, RetrieveCollectionsResponse)
                assert result.total == 1
                assert result.offset == 0
                assert result.limit == 10
                assert len(result.collections) == 1
                mock_repository.get_collections_by_user.assert_called_once_with(
                    user_id=user_id, offset=0, limit=10
                )

        @pytest.mark.asyncio
        async def test_get_collections_failure(self, service, mock_repository):
            """異常系：コレクション一覧取得時の例外処理を確認する"""
            # Arrange
            user_id = "test_user"
            request = GetCollectionsRequest(offset=0, limit=10)
            mock_repository.get_collections_by_user.side_effect = Exception(
                "Database error"
            )

            # Act & Assert
            with pytest.raises(BaseAppError) as exc_info:
                await service.get_collections(user_id, request)

            assert "Failed to retrieve collections" in str(exc_info.value)

    class TestGetCollectionDetail:
        """get_collection_detailメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_collection_detail_success(
            self, service, mock_repository, sample_collection
        ):
            """正常系：コレクション詳細取得が成功することを確認する"""
            # Arrange
            public_collection_id = "test_id"
            user_id = "test_user"

            mock_repository.get_collection_with_documents.return_value = (
                sample_collection,
                [],
            )

            # Act
            with patch(
                "qines_gai_backend.modules.collections.models.CollectionDetail.from_db"
            ) as mock_from_db:
                expected_result = CollectionDetail(
                    public_collection_id="test_id",
                    name="Test Collection",
                    documents=[],
                    created_at=datetime(2023, 1, 1),
                    updated_at=datetime(2023, 1, 1),
                )
                mock_from_db.return_value = expected_result

                result = await service.get_collection_detail(
                    public_collection_id, user_id
                )

                # Assert
                assert result == expected_result
                mock_repository.get_collection_with_documents.assert_called_once_with(
                    public_collection_id, user_id
                )

        @pytest.mark.asyncio
        async def test_get_collection_detail_not_found(self, service, mock_repository):
            """異常系：コレクションが見つからない場合の例外処理を確認する"""
            # Arrange
            public_collection_id = "nonexistent_id"
            user_id = "test_user"
            mock_repository.get_collection_with_documents.side_effect = (
                CollectionNotFoundError()
            )

            # Act & Assert
            with pytest.raises(CollectionNotFoundError):
                await service.get_collection_detail(public_collection_id, user_id)

        @pytest.mark.asyncio
        async def test_get_collection_detail_not_authorized(
            self, service, mock_repository
        ):
            """異常系：権限がない場合の例外処理を確認する"""
            # Arrange
            public_collection_id = "test_id"
            user_id = "unauthorized_user"
            mock_repository.get_collection_with_documents.side_effect = (
                NotAuthorizedCollectionError()
            )

            # Act & Assert
            with pytest.raises(NotAuthorizedCollectionError):
                await service.get_collection_detail(public_collection_id, user_id)

        @pytest.mark.asyncio
        async def test_get_collection_detail_failure(self, service, mock_repository):
            """異常系：コレクション詳細取得時の例外処理を確認する"""
            # Arrange
            public_collection_id = "test_id"
            user_id = "test_user"
            mock_repository.get_collection_with_documents.side_effect = Exception(
                "Database error"
            )

            # Act & Assert
            with pytest.raises(BaseAppError) as exc_info:
                await service.get_collection_detail(public_collection_id, user_id)

            assert "Failed to retrieve collection detail" in str(exc_info.value)

    class TestUpdateCollection:
        """update_collectionメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_update_collection_success(
            self, service, mock_repository, sample_collection
        ):
            """正常系：コレクション更新が成功することを確認する"""
            # Arrange
            public_collection_id = "test_id"
            user_id = "test_user"
            request = CreateCollectionRequest(
                name="Updated Collection", document_ids=[str(uuid.uuid4())]
            )

            mock_repository.get_collection_by_public_id.return_value = sample_collection
            mock_repository.get_collection_with_documents.return_value = (
                sample_collection,
                [],
            )

            # Act
            with patch(
                "qines_gai_backend.modules.collections.models.CollectionDetail.from_db"
            ) as mock_from_db:
                expected_result = CollectionDetail(
                    public_collection_id="test_id",
                    name="Updated Collection",
                    documents=[],
                    created_at=datetime(2023, 1, 1),
                    updated_at=datetime(2023, 1, 1),
                )
                mock_from_db.return_value = expected_result

                result = await service.update_collection(
                    public_collection_id, user_id, request
                )

                # Assert
                assert result == expected_result
                mock_repository.get_collection_by_public_id.assert_called_once_with(
                    public_collection_id, user_id
                )
                mock_repository.update_collection.assert_called_once()
                mock_repository.commit.assert_called_once()

        @pytest.mark.asyncio
        async def test_update_collection_not_found(self, service, mock_repository):
            """異常系：コレクションが見つからない場合の例外処理を確認する"""
            # Arrange
            public_collection_id = "nonexistent_id"
            user_id = "test_user"
            request = CreateCollectionRequest(
                name="Updated Collection", document_ids=[]
            )
            mock_repository.get_collection_by_public_id.side_effect = (
                CollectionNotFoundError()
            )

            # Act & Assert
            with pytest.raises(CollectionNotFoundError):
                await service.update_collection(public_collection_id, user_id, request)

            mock_repository.rollback.assert_called_once()

        @pytest.mark.asyncio
        async def test_update_collection_not_authorized(self, service, mock_repository):
            """異常系：権限がない場合の例外処理を確認する"""
            # Arrange
            public_collection_id = "test_id"
            user_id = "unauthorized_user"
            request = CreateCollectionRequest(
                name="Updated Collection", document_ids=[]
            )
            mock_repository.get_collection_by_public_id.side_effect = (
                NotAuthorizedCollectionError()
            )

            # Act & Assert
            with pytest.raises(NotAuthorizedCollectionError):
                await service.update_collection(public_collection_id, user_id, request)

            mock_repository.rollback.assert_called_once()

        @pytest.mark.asyncio
        async def test_update_collection_failure(
            self, service, mock_repository, sample_collection
        ):
            """異常系：コレクション更新時の例外処理を確認する"""
            # Arrange
            public_collection_id = "test_id"
            user_id = "test_user"
            request = CreateCollectionRequest(
                name="Updated Collection", document_ids=[]
            )

            mock_repository.get_collection_by_public_id.return_value = sample_collection
            mock_repository.update_collection.side_effect = Exception("Database error")

            # Act & Assert
            with pytest.raises(BaseAppError) as exc_info:
                await service.update_collection(public_collection_id, user_id, request)

            assert "Failed to update collection" in str(exc_info.value)
            mock_repository.rollback.assert_called_once()

    class TestGetCollectionConversations:
        """get_collection_conversationsメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_collection_conversations_success(
            self, service, mock_repository, sample_collection, sample_conversation
        ):
            """正常系：コレクション会話履歴一覧取得が成功することを確認する"""
            # Arrange
            public_collection_id = "test_id"
            user_id = "test_user"

            mock_repository.get_collection_by_public_id.return_value = sample_collection
            mock_repository.get_conversations_by_collection.return_value = [
                sample_conversation
            ]

            # Act
            result = await service.get_collection_conversations(
                public_collection_id, user_id
            )

            # Assert
            assert len(result) == 1
            assert isinstance(result[0], ConversationBase)
            assert result[0].public_conversation_id == "conv_id"
            assert result[0].title == "Test Conversation"

            mock_repository.get_collection_by_public_id.assert_called_once_with(
                public_collection_id, user_id
            )
            mock_repository.get_conversations_by_collection.assert_called_once_with(
                sample_collection.collection_id, user_id
            )

        @pytest.mark.asyncio
        async def test_get_collection_conversations_not_found(
            self, service, mock_repository
        ):
            """異常系：コレクションが見つからない場合の例外処理を確認する"""
            # Arrange
            public_collection_id = "nonexistent_id"
            user_id = "test_user"
            mock_repository.get_collection_by_public_id.side_effect = (
                CollectionNotFoundError()
            )

            # Act & Assert
            with pytest.raises(CollectionNotFoundError):
                await service.get_collection_conversations(
                    public_collection_id, user_id
                )

        @pytest.mark.asyncio
        async def test_get_collection_conversations_not_authorized(
            self, service, mock_repository
        ):
            """異常系：権限がない場合の例外処理を確認する"""
            # Arrange
            public_collection_id = "test_id"
            user_id = "unauthorized_user"
            mock_repository.get_collection_by_public_id.side_effect = (
                NotAuthorizedCollectionError()
            )

            # Act & Assert
            with pytest.raises(NotAuthorizedCollectionError):
                await service.get_collection_conversations(
                    public_collection_id, user_id
                )

        @pytest.mark.asyncio
        async def test_get_collection_conversations_failure(
            self, service, mock_repository, sample_collection
        ):
            """異常系：会話履歴取得時の例外処理を確認する"""
            # Arrange
            public_collection_id = "test_id"
            user_id = "test_user"

            mock_repository.get_collection_by_public_id.return_value = sample_collection
            mock_repository.get_conversations_by_collection.side_effect = Exception(
                "Database error"
            )

            # Act & Assert
            with pytest.raises(BaseAppError) as exc_info:
                await service.get_collection_conversations(
                    public_collection_id, user_id
                )

            assert "Failed to retrieve collection conversations" in str(exc_info.value)
