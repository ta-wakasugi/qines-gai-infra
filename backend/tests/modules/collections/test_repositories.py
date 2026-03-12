import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from qines_gai_backend.modules.collections.repositories import CollectionRepository
from qines_gai_backend.shared.exceptions import (
    CollectionNotFoundError,
    NotAuthorizedCollectionError,
)


class TestCollectionRepository:
    """CollectionRepositoryのテストクラス"""

    class TestInit:
        """__init__メソッドのテストクラス"""

        def test_init_success(self):
            """初期化が正常に行われることを確認する"""
            mock_session = AsyncMock()
            repository = CollectionRepository(mock_session)
            assert repository.session is mock_session

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
                document_uuids = [doc1_id, doc2_id]

                # Repository を使ってコレクション作成
                repository = CollectionRepository(test_data_creator.session)
                result = await repository.create_collection(
                    "test_user", "Test Collection", document_uuids
                )

                # セッションをexpungeしてリレーションシップの自動読み込みを防ぐ
                test_data_creator.session.expunge(result)
                await test_data_creator.session.commit()

                # Assert（基本的なプロパティのみ確認）
                assert result is not None
                assert result.user_id == "test_user"
                assert result.name == "Test Collection"
                assert result.collection_id is not None

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_create_collection_with_empty_documents(self, test_data_creator):
            """ドキュメントなしでのコレクション作成を確認する"""
            try:
                repository = CollectionRepository(test_data_creator.session)
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

    class TestGetCollectionsByUser:
        """get_collections_by_userメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_collections_by_user_success(self, test_data_creator):
            """ユーザーのコレクション一覧取得が正常に行われることを確認する"""
            try:
                # 一意のユーザーIDを使用
                unique_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
                other_user_id = f"other_user_{uuid.uuid4().hex[:8]}"

                # テスト用コレクション作成
                collection1_id = await test_data_creator.create_test_collection(
                    user_id=unique_user_id, name="Collection 1"
                )
                collection2_id = await test_data_creator.create_test_collection(
                    user_id=unique_user_id, name="Collection 2"
                )
                await test_data_creator.create_test_collection(
                    user_id=other_user_id, name="Other Collection"
                )
                await test_data_creator.session.commit()

                # Repository を使ってコレクション一覧取得
                repository = CollectionRepository(test_data_creator.session)
                collections, total = await repository.get_collections_by_user(
                    unique_user_id
                )

                # Assert
                assert len(collections) == 2
                assert total == 2
                collection_ids = [c.collection_id for c in collections]
                assert collection1_id in collection_ids
                assert collection2_id in collection_ids

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_collections_by_user_with_pagination(self, test_data_creator):
            """ページネーション付きでのコレクション一覧取得を確認する"""
            try:
                # 一意のユーザーIDを使用
                unique_user_id = f"test_user_{uuid.uuid4().hex[:8]}"

                # 3つのコレクション作成
                for i in range(3):
                    await test_data_creator.create_test_collection(
                        user_id=unique_user_id, name=f"Collection {i + 1}"
                    )
                await test_data_creator.session.commit()

                repository = CollectionRepository(test_data_creator.session)
                collections, total = await repository.get_collections_by_user(
                    unique_user_id, offset=1, limit=1
                )

                # Assert
                assert len(collections) == 1
                assert total == 3

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_collections_by_user_no_results(self, test_data_creator):
            """存在しないユーザーでの一覧取得を確認する"""
            repository = CollectionRepository(test_data_creator.session)
            collections, total = await repository.get_collections_by_user(
                "nonexistent_user"
            )

            assert len(collections) == 0
            assert total == 0

    class TestGetCollectionByPublicId:
        """get_collection_by_public_idメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_collection_by_public_id_success(self, test_data_creator):
            """公開コレクションIDでの取得が正常に行われることを確認する"""
            try:
                # テスト用コレクション作成（11文字制限に合わせる）
                public_id = "test_pub01"  # 10文字
                collection_id = await test_data_creator.create_test_collection(
                    public_collection_id=public_id, user_id="test_user"
                )
                await test_data_creator.session.commit()

                # Repository を使ってコレクション取得
                repository = CollectionRepository(test_data_creator.session)
                result = await repository.get_collection_by_public_id(public_id)

                # Assert
                assert result is not None
                assert result.collection_id == collection_id
                assert result.public_collection_id == public_id

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_collection_by_public_id_with_user_authorization(
            self, test_data_creator
        ):
            """ユーザー権限チェック付きでの取得を確認する"""
            try:
                public_id = "test_auth1"  # 10文字
                await test_data_creator.create_test_collection(
                    public_collection_id=public_id, user_id="test_user"
                )
                await test_data_creator.session.commit()

                repository = CollectionRepository(test_data_creator.session)
                result = await repository.get_collection_by_public_id(
                    public_id, user_id="test_user"
                )

                assert result is not None
                assert result.user_id == "test_user"

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_collection_by_public_id_not_found(self, test_data_creator):
            """存在しない公開IDでの例外発生を確認する"""
            repository = CollectionRepository(test_data_creator.session)

            with pytest.raises(CollectionNotFoundError):
                await repository.get_collection_by_public_id("nonexistent_id")

        @pytest.mark.asyncio
        async def test_get_collection_by_public_id_unauthorized(
            self, test_data_creator
        ):
            """権限のないユーザーでの例外発生を確認する"""
            try:
                public_id = "test_unau1"  # 10文字
                await test_data_creator.create_test_collection(
                    public_collection_id=public_id, user_id="owner_user"
                )
                await test_data_creator.session.commit()

                repository = CollectionRepository(test_data_creator.session)

                with pytest.raises(NotAuthorizedCollectionError):
                    await repository.get_collection_by_public_id(
                        public_id, user_id="other_user"
                    )

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestGetCollectionWithDocuments:
        """get_collection_with_documentsメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_collection_with_documents_success(self, test_data_creator):
            """コレクションとドキュメント情報の一括取得を確認する"""
            try:
                # テストデータ準備
                doc1_id = await test_data_creator.create_test_document(
                    file_name="doc1.pdf"
                )
                doc2_id = await test_data_creator.create_test_document(
                    file_name="doc2.pdf"
                )
                public_id = "test_docs1"  # 10文字
                collection_id = await test_data_creator.create_test_collection(
                    public_collection_id=public_id
                )
                await test_data_creator.create_test_collection_document(
                    collection_id, doc1_id, position=1
                )
                await test_data_creator.create_test_collection_document(
                    collection_id, doc2_id, position=2
                )
                await test_data_creator.session.commit()

                # Repository を使って取得
                repository = CollectionRepository(test_data_creator.session)
                (
                    collection,
                    collection_documents,
                ) = await repository.get_collection_with_documents(public_id)

                # Assert
                assert collection is not None
                assert len(collection_documents) == 2
                assert collection_documents[0].position == 1
                assert collection_documents[1].position == 2
                # リレーションシップのアクセスを避けて基本的なプロパティのみ確認
                assert collection_documents[0].document_id == doc1_id
                assert collection_documents[1].document_id == doc2_id

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_collection_with_documents_no_documents(
            self, test_data_creator
        ):
            """ドキュメントがないコレクションの取得を確認する"""
            try:
                public_id = "test_nod1"  # 9文字
                await test_data_creator.create_test_collection(
                    public_collection_id=public_id
                )
                await test_data_creator.session.commit()

                repository = CollectionRepository(test_data_creator.session)
                (
                    collection,
                    collection_documents,
                ) = await repository.get_collection_with_documents(public_id)

                assert collection is not None
                assert len(collection_documents) == 0

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestUpdateCollection:
        """update_collectionメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_update_collection_success(self, test_data_creator):
            """コレクションの更新が正常に行われることを確認する"""
            try:
                # 初期データ準備
                doc1_id = await test_data_creator.create_test_document(
                    file_name="doc1.pdf"
                )
                doc2_id = await test_data_creator.create_test_document(
                    file_name="doc2.pdf"
                )
                doc3_id = await test_data_creator.create_test_document(
                    file_name="doc3.pdf"
                )

                collection_id = await test_data_creator.create_test_collection(
                    name="Old Name"
                )
                await test_data_creator.create_test_collection_document(
                    collection_id, doc1_id, position=1
                )
                await test_data_creator.session.commit()

                # 更新実行
                repository = CollectionRepository(test_data_creator.session)
                await repository.update_collection(
                    collection_id, "New Name", [doc2_id, doc3_id]
                )
                await test_data_creator.session.commit()

                # 結果確認のためコレクションとドキュメント取得
                from sqlalchemy import select
                from qines_gai_backend.schemas.schema import (
                    T_Collection,
                    T_CollectionDocument,
                )

                # コレクション名の確認
                result = await test_data_creator.session.execute(
                    select(T_Collection).filter_by(collection_id=collection_id)
                )
                updated_collection = result.unique().scalar()
                assert updated_collection.name == "New Name"

                # ドキュメント関連の確認
                result = await test_data_creator.session.execute(
                    select(T_CollectionDocument)
                    .filter_by(collection_id=collection_id)
                    .order_by(T_CollectionDocument.position)
                )
                collection_docs = result.unique().scalars().all()
                assert len(collection_docs) == 2
                assert collection_docs[0].document_id == doc2_id
                assert collection_docs[0].position == 1
                assert collection_docs[1].document_id == doc3_id
                assert collection_docs[1].position == 2

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_update_collection_with_existing_documents(
            self, test_data_creator
        ):
            """既存ドキュメントを含む更新を確認する"""
            try:
                # 初期データ準備
                doc1_id = await test_data_creator.create_test_document(
                    file_name="doc1.pdf"
                )
                doc2_id = await test_data_creator.create_test_document(
                    file_name="doc2.pdf"
                )

                collection_id = await test_data_creator.create_test_collection(
                    name="Test Collection"
                )
                await test_data_creator.create_test_collection_document(
                    collection_id, doc1_id, position=1
                )
                await test_data_creator.create_test_collection_document(
                    collection_id, doc2_id, position=2
                )
                await test_data_creator.session.commit()

                # doc2, doc1の順番で更新（順序変更）
                repository = CollectionRepository(test_data_creator.session)
                await repository.update_collection(
                    collection_id, "Updated Collection", [doc2_id, doc1_id]
                )
                await test_data_creator.session.commit()

                # 結果確認
                from sqlalchemy import select
                from qines_gai_backend.schemas.schema import T_CollectionDocument

                result = await test_data_creator.session.execute(
                    select(T_CollectionDocument)
                    .filter_by(collection_id=collection_id)
                    .order_by(T_CollectionDocument.position)
                )
                collection_docs = result.unique().scalars().all()
                assert len(collection_docs) == 2
                assert collection_docs[0].document_id == doc2_id
                assert collection_docs[0].position == 1
                assert collection_docs[1].document_id == doc1_id
                assert collection_docs[1].position == 2

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_update_collection_remove_all_documents(self, test_data_creator):
            """全てのドキュメントを削除する更新を確認する"""
            try:
                # 初期データ準備
                doc1_id = await test_data_creator.create_test_document()
                collection_id = await test_data_creator.create_test_collection()
                await test_data_creator.create_test_collection_document(
                    collection_id, doc1_id
                )
                await test_data_creator.session.commit()

                # 空のドキュメントリストで更新
                repository = CollectionRepository(test_data_creator.session)
                await repository.update_collection(
                    collection_id, "Empty Collection", []
                )
                await test_data_creator.session.commit()

                # 結果確認
                from sqlalchemy import select
                from qines_gai_backend.schemas.schema import T_CollectionDocument

                result = await test_data_creator.session.execute(
                    select(T_CollectionDocument).filter_by(collection_id=collection_id)
                )
                collection_docs = result.unique().scalars().all()
                assert len(collection_docs) == 0

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestGetConversationsByCollection:
        """get_conversations_by_collectionメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_conversations_by_collection_success(self, test_data_creator):
            """コレクションに紐づく会話履歴の取得を確認する"""
            try:
                # テストデータ準備
                collection_id = await test_data_creator.create_test_collection()
                conv1_id = await test_data_creator.create_test_conversation(
                    collection_id, user_id="test_user", title="Conversation 1"
                )
                conv2_id = await test_data_creator.create_test_conversation(
                    collection_id, user_id="test_user", title="Conversation 2"
                )
                # 削除済み会話履歴
                await test_data_creator.create_test_conversation(
                    collection_id, user_id="test_user", title="Deleted", is_deleted=True
                )
                # 他のユーザーの会話履歴
                await test_data_creator.create_test_conversation(
                    collection_id, user_id="other_user", title="Other User"
                )
                await test_data_creator.session.commit()

                # Repository を使って取得
                repository = CollectionRepository(test_data_creator.session)
                conversations = await repository.get_conversations_by_collection(
                    collection_id, "test_user"
                )

                # Assert
                assert len(conversations) == 2
                conversation_ids = [conv.conversation_id for conv in conversations]
                assert conv1_id in conversation_ids
                assert conv2_id in conversation_ids

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_conversations_by_collection_no_results(
            self, test_data_creator
        ):
            """会話履歴がない場合の取得を確認する"""
            try:
                collection_id = await test_data_creator.create_test_collection()
                await test_data_creator.session.commit()

                repository = CollectionRepository(test_data_creator.session)
                conversations = await repository.get_conversations_by_collection(
                    collection_id, "test_user"
                )

                assert len(conversations) == 0

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestCommit:
        """commitメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_commit_success(self, test_data_creator):
            """コミットが正常に行われることを確認する"""
            repository = CollectionRepository(test_data_creator.session)

            # session.commit のモックを作成して呼び出しを確認
            with patch.object(
                test_data_creator.session, "commit", new_callable=AsyncMock
            ) as mock_commit:
                await repository.commit()
                mock_commit.assert_called_once()

        @pytest.mark.asyncio
        async def test_commit_with_exception(self, test_data_creator):
            """コミット時の例外処理を確認する"""
            repository = CollectionRepository(test_data_creator.session)

            # session.commit で例外発生をモック
            with patch.object(
                test_data_creator.session, "commit", new_callable=AsyncMock
            ) as mock_commit:
                mock_commit.side_effect = SQLAlchemyError("Commit failed")

                with pytest.raises(SQLAlchemyError):
                    await repository.commit()

    class TestRollback:
        """rollbackメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_rollback_success(self, test_data_creator):
            """ロールバックが正常に行われることを確認する"""
            repository = CollectionRepository(test_data_creator.session)

            # session.rollback のモックを作成して呼び出しを確認
            with patch.object(
                test_data_creator.session, "rollback", new_callable=AsyncMock
            ) as mock_rollback:
                await repository.rollback()
                mock_rollback.assert_called_once()

        @pytest.mark.asyncio
        async def test_rollback_with_exception(self, test_data_creator):
            """ロールバック時の例外処理を確認する"""
            repository = CollectionRepository(test_data_creator.session)

            # session.rollback で例外発生をモック
            with patch.object(
                test_data_creator.session, "rollback", new_callable=AsyncMock
            ) as mock_rollback:
                mock_rollback.side_effect = SQLAlchemyError("Rollback failed")

                with pytest.raises(SQLAlchemyError):
                    await repository.rollback()
