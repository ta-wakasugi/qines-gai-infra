import uuid

import pytest
from sqlalchemy.exc import SQLAlchemyError

from qines_gai_backend.modules.conversations.repositories import ConversationRepository


class TestConversationRepository:
    """ConversationRepositoryのテストクラス"""

    class TestGetConversationByPublicId:
        """get_conversation_by_public_idメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_conversation_by_public_id_success(self, test_data_creator):
            """公開会話履歴IDで会話履歴を正常に取得できることを確認する"""
            try:
                # テストデータを作成
                collection_id = await test_data_creator.create_test_collection()
                public_conversation_id = "test_succes"  # 11文字以内
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id, public_conversation_id=public_conversation_id
                )
                await test_data_creator.session.commit()

                # Repository を使って会話履歴を取得
                repository = ConversationRepository(test_data_creator.session)
                result = await repository.get_conversation_by_public_id(
                    public_conversation_id
                )

                # Assert
                assert result is not None
                assert result.public_conversation_id == public_conversation_id
                assert result.conversation_id == conversation_id
                assert result.is_deleted is False

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_conversation_by_public_id_not_found(self, test_data_creator):
            """存在しない公開会話履歴IDで会話履歴が見つからない場合のテスト"""
            # Repository を使って存在しない会話履歴を取得
            repository = ConversationRepository(test_data_creator.session)
            result = await repository.get_conversation_by_public_id("nonexistent_id")

            # Assert
            assert result is None

        @pytest.mark.asyncio
        async def test_get_conversation_by_public_id_with_deleted_conversation(
            self, test_data_creator
        ):
            """削除された会話履歴は取得されないことを確認する"""
            try:
                # 削除された会話履歴を作成
                collection_id = await test_data_creator.create_test_collection()
                public_conversation_id = "test_delet"  # 11文字以内
                await test_data_creator.create_test_conversation(
                    collection_id,
                    public_conversation_id=public_conversation_id,
                    is_deleted=True,
                )
                await test_data_creator.session.commit()

                # Repository を使って削除された会話履歴を取得
                repository = ConversationRepository(test_data_creator.session)
                result = await repository.get_conversation_by_public_id(
                    public_conversation_id
                )

                # Assert (削除された会話履歴は取得されない)
                assert result is None

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestGetMessageById:
        """get_message_by_idメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_message_by_id_success(self, test_data_creator):
            """会話履歴IDに紐づくメッセージ一覧を正常に取得できることを確認する"""
            try:
                # テストデータを作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id
                )

                # 複数のメッセージを作成（作成日時順のテストのため）
                message_id_1 = await test_data_creator.create_test_message(
                    conversation_id, sender_type="user", content="First message"
                )
                message_id_2 = await test_data_creator.create_test_message(
                    conversation_id, sender_type="ai", content="Second message"
                )
                await test_data_creator.session.commit()

                # Repository を使ってメッセージ一覧を取得
                repository = ConversationRepository(test_data_creator.session)
                result = await repository.get_message_by_id(str(conversation_id))

                # Assert
                assert len(result) == 2
                assert result[0].message_id == message_id_1
                assert result[1].message_id == message_id_2
                assert result[0].sender_type == "user"
                assert result[1].sender_type == "ai"
                assert result[0].content == "First message"
                assert result[1].content == "Second message"

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_message_by_id_empty_result(self, test_data_creator):
            """メッセージが存在しない場合に空のリストが返されることを確認する"""
            try:
                # メッセージのない会話履歴を作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id
                )
                await test_data_creator.session.commit()

                # Repository を使ってメッセージ一覧を取得
                repository = ConversationRepository(test_data_creator.session)
                result = await repository.get_message_by_id(str(conversation_id))

                # Assert
                assert result == []

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_message_by_id_nonexistent_conversation(
            self, test_data_creator
        ):
            """存在しない会話履歴IDの場合に空のリストが返されることを確認する"""
            # Repository を使って存在しない会話履歴のメッセージを取得
            repository = ConversationRepository(test_data_creator.session)
            nonexistent_id = str(uuid.uuid4())
            result = await repository.get_message_by_id(nonexistent_id)

            # Assert
            assert result == []

        @pytest.mark.asyncio
        async def test_get_message_by_id_order_by_created_at(self, test_data_creator):
            """メッセージが作成日時順で取得されることを確認する"""
            try:
                # テストデータを作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id
                )

                # 意図的に順序を逆にしてメッセージを作成
                await test_data_creator.create_test_message(
                    conversation_id, sender_type="ai", content="Second message"
                )
                await test_data_creator.create_test_message(
                    conversation_id, sender_type="user", content="First message"
                )
                await test_data_creator.session.commit()

                # Repository を使ってメッセージ一覧を取得
                repository = ConversationRepository(test_data_creator.session)
                result = await repository.get_message_by_id(str(conversation_id))

                # Assert - created_at順で取得されることを確認
                assert len(result) == 2
                # 作成日時順（古い順）になっていることを確認
                assert result[0].created_at <= result[1].created_at

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

    class TestGetArtifactById:
        """get_artifact_by_idメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_artifact_by_id_success(self, test_data_creator):
            """会話履歴IDに紐づく成果物一覧を正常に取得できることを確認する"""
            try:
                # テストデータを作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id
                )
                message_id = await test_data_creator.create_test_message(
                    conversation_id
                )

                # 複数の成果物を作成
                artifact_id_1 = await test_data_creator.create_test_artifact(
                    conversation_id, message_id, title="First Artifact", version=1
                )
                artifact_id_2 = await test_data_creator.create_test_artifact(
                    conversation_id, message_id, title="Second Artifact", version=2
                )
                await test_data_creator.session.commit()

                # Repository を使って成果物一覧を取得
                repository = ConversationRepository(test_data_creator.session)
                result = await repository.get_artifact_by_id(str(conversation_id))

                # Assert
                assert len(result) == 2
                assert result[0].artifact_version_id == artifact_id_1
                assert result[1].artifact_version_id == artifact_id_2
                assert result[0].title == "First Artifact"
                assert result[1].title == "Second Artifact"
                assert result[0].version == 1
                assert result[1].version == 2

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_artifact_by_id_empty_result(self, test_data_creator):
            """成果物が存在しない場合に空のリストが返されることを確認する"""
            try:
                # 成果物のない会話履歴を作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id
                )
                await test_data_creator.session.commit()

                # Repository を使って成果物一覧を取得
                repository = ConversationRepository(test_data_creator.session)
                result = await repository.get_artifact_by_id(str(conversation_id))

                # Assert
                assert result == []

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_artifact_by_id_nonexistent_conversation(
            self, test_data_creator
        ):
            """存在しない会話履歴IDの場合に空のリストが返されることを確認する"""
            # Repository を使って存在しない会話履歴の成果物を取得
            repository = ConversationRepository(test_data_creator.session)
            nonexistent_id = str(uuid.uuid4())
            result = await repository.get_artifact_by_id(nonexistent_id)

            # Assert
            assert result == []

        @pytest.mark.asyncio
        async def test_get_artifact_by_id_order_by_created_at(self, test_data_creator):
            """成果物が作成日時順で取得されることを確認する"""
            try:
                # テストデータを作成
                collection_id = await test_data_creator.create_test_collection()
                conversation_id = await test_data_creator.create_test_conversation(
                    collection_id
                )
                message_id = await test_data_creator.create_test_message(
                    conversation_id
                )

                # 意図的に順序を逆にして成果物を作成
                await test_data_creator.create_test_artifact(
                    conversation_id, message_id, title="Second Artifact", version=2
                )
                await test_data_creator.create_test_artifact(
                    conversation_id, message_id, title="First Artifact", version=1
                )
                await test_data_creator.session.commit()

                # Repository を使って成果物一覧を取得
                repository = ConversationRepository(test_data_creator.session)
                result = await repository.get_artifact_by_id(str(conversation_id))

                # Assert - created_at順で取得されることを確認
                assert len(result) == 2
                # 作成日時順（古い順）になっていることを確認
                assert result[0].created_at <= result[1].created_at

            except SQLAlchemyError:
                await test_data_creator.session.rollback()
                raise
