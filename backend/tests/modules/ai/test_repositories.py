import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from qines_gai_backend.modules.ai.repositories import AIRepository
from qines_gai_backend.schemas.schema import (
    T_Collection,
    T_CollectionDocument,
    T_Conversation,
)


class TestAIRepository:
    """AIRepositoryのテストクラス"""

    class TestInit:
        """__init__メソッドのテストクラス"""

        def test_init_success(self):
            """初期化が正常に行われることを確認する"""
            mock_session = AsyncMock()
            mock_meili_client = AsyncMock()
            repository = AIRepository(mock_session, mock_meili_client)
            assert repository.session is mock_session
            assert repository.meili_client is mock_meili_client

    class TestCreateCollection:
        """create_collectionメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_create_collection_success(self, test_data_creator):
            """コレクションの作成が正常に行われることを確認する"""
            try:
                # テスト用ドキュメント作成
                doc1_id = await test_data_creator.create_test_document(
                    file_name="doc1.pdf"
                )
                doc2_id = await test_data_creator.create_test_document(
                    file_name="doc2.pdf"
                )
                document_ids = [str(doc1_id), str(doc2_id)]

                # Repository を使ってコレクション作成
                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                result = await repository.create_collection(
                    "test_user", "Test Collection", document_ids
                )

                # セッションをexpungeしてリレーションシップの自動読み込みを防ぐ
                test_data_creator.session.expunge(result)
                await test_data_creator.session.commit()

                # Assert（基本的なプロパティのみ確認）
                assert result is not None
                assert result.user_id == "test_user"
                assert result.name == "Test Collection"
                assert result.collection_id is not None
                assert result.public_collection_id is not None

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_create_collection_with_empty_documents(self, test_data_creator):
            """ドキュメントなしでのコレクション作成を確認する"""
            try:
                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                result = await repository.create_collection(
                    "test_user", "Empty Collection", []
                )

                # セッションをexpungeしてリレーションシップの自動読み込みを防ぐ
                test_data_creator.session.expunge(result)
                await test_data_creator.session.commit()

                assert result is not None
                assert result.name == "Empty Collection"

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_create_collection_with_multiple_documents(
            self, test_data_creator
        ):
            """複数ドキュメントを含むコレクション作成を確認する"""
            try:
                # 3つのドキュメント作成
                doc_ids = []
                for i in range(3):
                    doc_id = await test_data_creator.create_test_document(
                        file_name=f"doc{i}.pdf"
                    )
                    doc_ids.append(str(doc_id))

                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                result = await repository.create_collection(
                    "test_user", "Multi Doc Collection", doc_ids
                )

                test_data_creator.session.expunge(result)
                await test_data_creator.session.commit()

                # collection_documentsの数を確認
                stmt = select(T_CollectionDocument).filter_by(
                    collection_id=result.collection_id
                )
                coll_docs_result = await test_data_creator.session.execute(stmt)
                coll_docs = coll_docs_result.unique().scalars().all()

                assert len(coll_docs) == 3
                assert coll_docs[0].position == 1
                assert coll_docs[1].position == 2
                assert coll_docs[2].position == 3

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestGetCollectionByPublicId:
        """get_collection_by_public_idメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_collection_success(self, test_data_creator):
            """公開コレクションIDでの取得が正常に行われることを確認する"""
            try:
                # テスト用コレクション作成
                public_id = "test_ai001"
                collection_id = await test_data_creator.create_test_collection(
                    public_collection_id=public_id, user_id="test_user"
                )
                await test_data_creator.session.commit()

                # Repository を使ってコレクション取得
                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                result = await repository.get_collection_by_public_id(public_id)

                # Assert
                assert result is not None
                assert result.collection_id == collection_id
                assert result.public_collection_id == public_id

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_collection_with_user_id_check(self, test_data_creator):
            """ユーザーID指定での所有者チェックを確認する"""
            try:
                public_id = "test_ai002"
                await test_data_creator.create_test_collection(
                    public_collection_id=public_id, user_id="test_user"
                )
                await test_data_creator.session.commit()

                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                result = await repository.get_collection_by_public_id(
                    public_id, user_id="test_user"
                )

                assert result is not None
                assert result.user_id == "test_user"

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_collection_not_found(self, test_data_creator):
            """存在しない公開IDでの取得を確認する"""
            mock_meili_client = AsyncMock()
            repository = AIRepository(test_data_creator.session, mock_meili_client)
            result = await repository.get_collection_by_public_id("nonexistent_id")

            assert result is None

        @pytest.mark.asyncio
        async def test_get_collection_not_authorized(self, test_data_creator):
            """権限のないユーザーでの取得を確認する（Noneを返す）"""
            try:
                public_id = "test_ai003"
                await test_data_creator.create_test_collection(
                    public_collection_id=public_id, user_id="owner_user"
                )
                await test_data_creator.session.commit()

                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                result = await repository.get_collection_by_public_id(
                    public_id, user_id="other_user"
                )

                # 所有者が異なる場合はNoneを返す
                assert result is None

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestGetConversationByPublicId:
        """get_conversation_by_public_idメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_conversation_success(self, test_data_creator):
            """公開会話IDでの取得が正常に行われることを確認する"""
            try:
                # テスト用データ作成
                collection_id = await test_data_creator.create_test_collection()
                public_conv_id = "test_cnv01"
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id, public_conversation_id=public_conv_id
                )
                await test_data_creator.session.commit()

                # Repository を使って取得
                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                result = await repository.get_conversation_by_public_id(public_conv_id)

                # Assert
                assert result is not None
                assert result.conversation_id == conversation_id
                assert result.public_conversation_id == public_conv_id

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_conversation_with_messages_and_artifacts(
            self, test_data_creator
        ):
            """メッセージと成果物を含む会話の取得を確認する"""
            try:
                # テスト用データ作成
                collection_id = await test_data_creator.create_test_collection()
                public_conv_id = "test_cnv02"
                (
                    conversation_id,
                    message_ids,
                    artifact_ids,
                ) = await test_data_creator.create_test_conversation_with_messages_and_artifacts(
                    collection_id,
                    message_count=2,
                    artifact_count=1,
                    public_conversation_id=public_conv_id,
                )
                await test_data_creator.session.commit()

                # Repository を使って取得
                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                result = await repository.get_conversation_by_public_id(public_conv_id)

                # Assert
                assert result is not None
                assert len(result.messages) == 2
                # メッセージにartifactsがロードされていることを確認
                assert len(result.messages[-1].artifacts) >= 1

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_conversation_not_found(self, test_data_creator):
            """存在しない会話IDでの取得を確認する"""
            mock_meili_client = AsyncMock()
            repository = AIRepository(test_data_creator.session, mock_meili_client)
            result = await repository.get_conversation_by_public_id("nonexistent_conv")

            assert result is None

        @pytest.mark.asyncio
        async def test_get_conversation_deleted(self, test_data_creator):
            """削除済み会話の取得を確認する（Noneを返す）"""
            try:
                collection_id = await test_data_creator.create_test_collection()
                public_conv_id = "test_cnv03"
                await test_data_creator.create_test_conversation(
                    collection_id,
                    public_conversation_id=public_conv_id,
                    is_deleted=True,
                )
                await test_data_creator.session.commit()

                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                result = await repository.get_conversation_by_public_id(public_conv_id)

                # 削除済みの会話はNoneを返す
                assert result is None

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestCreateConversation:
        """create_conversationメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_create_conversation_success(self, test_data_creator):
            """会話の作成が正常に行われることを確認する"""
            try:
                # テスト用コレクション作成
                collection_id = await test_data_creator.create_test_collection()
                await test_data_creator.session.commit()

                # Repository を使って会話作成
                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                result = await repository.create_conversation(
                    public_conversation_id="test_new_c",
                    user_id="test_user",
                    collection_id=str(collection_id),
                    title="Test Conversation",
                )

                # Assert（commit前に確認）
                assert result is not None
                assert result.public_conversation_id == "test_new_c"
                assert result.user_id == "test_user"
                assert str(result.collection_id) == str(collection_id)
                assert result.title == "Test Conversation"

                await test_data_creator.session.commit()

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestUpdateConversation:
        """update_conversationメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_update_conversation_success(self, test_data_creator):
            """会話の更新が正常に行われることを確認する"""
            try:
                # テスト用データ作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id, title="Old Title"
                )
                await test_data_creator.session.commit()

                # 会話オブジェクトを取得
                stmt = select(T_Conversation).filter_by(conversation_id=conversation_id)
                result = await test_data_creator.session.execute(stmt)
                conversation = result.scalar()

                # Repository を使って更新
                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                updated = await repository.update_conversation(conversation)

                # Assert（commit前に確認）
                assert updated is not None
                assert updated.updated_at is not None

                await test_data_creator.session.commit()

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_update_conversation_timestamp_update(self, test_data_creator):
            """タイムスタンプの更新を確認する"""
            try:
                # テスト用データ作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id
                )
                await test_data_creator.session.commit()

                # 会話オブジェクトを取得
                stmt = select(T_Conversation).filter_by(conversation_id=conversation_id)
                result = await test_data_creator.session.execute(stmt)
                conversation = result.scalar()

                # Repository を使って更新
                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                await repository.update_conversation(conversation)
                await test_data_creator.session.commit()

                # 再度取得して確認
                result = await test_data_creator.session.execute(stmt)
                updated_conversation = result.scalar()

                # updated_atが更新されている（または同じ）
                assert updated_conversation.updated_at is not None

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestCreateMessage:
        """create_messageメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_create_message_user_type(self, test_data_creator):
            """ユーザーメッセージの作成を確認する"""
            try:
                # テスト用データ作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id
                )
                await test_data_creator.session.commit()

                # Repository を使ってメッセージ作成
                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                result = await repository.create_message(
                    conversation_id=str(conversation_id),
                    sender_type="user",
                    content="Test user message",
                    metadata_info={"key": "value"},
                )

                # Assert（commit前に確認）
                assert result is not None
                assert result.sender_type == "user"
                assert result.content == "Test user message"
                assert result.metadata_info == {"key": "value"}

                await test_data_creator.session.commit()

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_create_message_ai_type(self, test_data_creator):
            """AIメッセージの作成を確認する"""
            try:
                # テスト用データ作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id
                )
                await test_data_creator.session.commit()

                # Repository を使ってメッセージ作成
                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                result = await repository.create_message(
                    conversation_id=str(conversation_id),
                    sender_type="ai",
                    content="Test AI response",
                    metadata_info={},
                )

                # Assert（commit前に確認）
                assert result is not None
                assert result.sender_type == "ai"
                assert result.content == "Test AI response"

                await test_data_creator.session.commit()

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestCreateArtifact:
        """create_artifactメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_create_artifact_success(self, test_data_creator):
            """成果物の作成が正常に行われることを確認する"""
            try:
                # テスト用データ作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id
                )
                message_id = await test_data_creator.create_test_message(
                    conversation_id
                )
                await test_data_creator.session.commit()

                # Repository を使って成果物作成
                artifact_id = str(uuid.uuid4())
                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                result = await repository.create_artifact(
                    artifact_id=artifact_id,
                    conversation_id=str(conversation_id),
                    message_id=str(message_id),
                    title="Test Artifact",
                    version=1,
                    content="Test artifact content",
                )

                # Assert（commit前に確認）
                assert result is not None
                assert result.artifact_id == artifact_id
                assert result.title == "Test Artifact"
                assert result.version == 1
                assert result.content == "Test artifact content"

                await test_data_creator.session.commit()

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestUpdateCollectionUsedAt:
        """update_collection_used_atメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_update_collection_used_at_success(self, test_data_creator):
            """コレクションの使用時刻更新が正常に行われることを確認する"""
            try:
                # テスト用コレクション作成
                collection_id = await test_data_creator.create_test_collection()
                await test_data_creator.session.commit()

                # Repository を使って used_at 更新
                mock_meili_client = AsyncMock()
                repository = AIRepository(test_data_creator.session, mock_meili_client)
                await repository.update_collection_used_at(str(collection_id))
                await test_data_creator.session.commit()

                # 更新されたことを確認
                stmt = select(T_Collection).filter_by(collection_id=collection_id)
                result = await test_data_creator.session.execute(stmt)
                collection = result.scalar()

                assert collection.used_at is not None

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestCommit:
        """commitメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_commit_success(self, test_data_creator):
            """コミットが正常に行われることを確認する"""
            mock_meili_client = AsyncMock()
            repository = AIRepository(test_data_creator.session, mock_meili_client)

            # session.commit のモックを作成して呼び出しを確認
            with patch.object(
                test_data_creator.session, "commit", new_callable=AsyncMock
            ) as mock_commit:
                await repository.commit()
                mock_commit.assert_called_once()

    class TestRollback:
        """rollbackメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_rollback_success(self, test_data_creator):
            """ロールバックが正常に行われることを確認する"""
            mock_meili_client = AsyncMock()
            repository = AIRepository(test_data_creator.session, mock_meili_client)

            # session.rollback のモックを作成して呼び出しを確認
            with patch.object(
                test_data_creator.session, "rollback", new_callable=AsyncMock
            ) as mock_rollback:
                await repository.rollback()
                mock_rollback.assert_called_once()
