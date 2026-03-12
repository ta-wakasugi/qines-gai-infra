import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from qines_gai_backend.modules.ai.models import ChatCompletionsRequest, ChatRequestBase
from qines_gai_backend.modules.ai.repositories import AIRepository
from qines_gai_backend.modules.ai.services import AIService
from qines_gai_backend.modules.collections.models import CollectionDetail
from qines_gai_backend.schemas.schema import T_Collection, T_Conversation
from qines_gai_backend.shared.exceptions import (
    CollectionCreationError,
)


class TestAIService:
    """AIServiceのテストクラス"""

    @pytest.fixture
    def mock_repository(self):
        """AIRepositoryのモックを作成する"""
        repo = AsyncMock(spec=AIRepository)
        repo.meili_client = MagicMock()
        repo.session = MagicMock()
        return repo

    @pytest.fixture
    def service(self, mock_repository):
        """AIServiceのインスタンスを作成する"""
        return AIService(mock_repository)

    @pytest.fixture
    def sample_collection(self):
        """テスト用のコレクションを作成する"""
        collection = MagicMock(spec=T_Collection)
        collection.collection_id = uuid.uuid4()
        collection.public_collection_id = "test_col01"
        collection.name = "Test AI Collection"
        collection.created_at = datetime(2023, 1, 1)
        collection.updated_at = datetime(2023, 1, 1)
        collection.user_id = "test_user"
        return collection

    @pytest.fixture
    def sample_conversation(self):
        """テスト用の会話を作成する"""
        conversation = MagicMock(spec=T_Conversation)
        conversation.conversation_id = uuid.uuid4()
        conversation.public_conversation_id = "test_conv01"
        conversation.title = "Test Conversation"
        conversation.user_id = "test_user"
        conversation.collection_id = str(uuid.uuid4())
        conversation.messages = []
        return conversation

    class TestInit:
        """__init__メソッドのテストクラス"""

        def test_init_success(self, mock_repository):
            """初期化が正常に行われることを確認する"""
            service = AIService(mock_repository)
            assert service.repository is mock_repository

    class TestCreateInitialCollection:
        """create_initial_collectionメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_create_initial_collection_success(
            self, service, mock_repository, sample_collection
        ):
            """正常系：初期コレクション作成が成功することを確認する"""
            # Arrange
            user_id = "test_user"
            request = ChatRequestBase(message="CAN仕様について教えて")

            # InitCollectionAgentのモック
            mock_agent_response = json.dumps(
                {
                    "document_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
                    "name": "CAN仕様コレクション",
                }
            )

            # is_document_accesibleのモック（全てアクセス可能）
            mock_is_accessible = AsyncMock(return_value=True)

            # Repositoryのモック
            mock_repository.create_collection.return_value = sample_collection
            mock_repository.get_collection_by_public_id.return_value = sample_collection

            # Act
            with patch(
                "qines_gai_backend.modules.ai.services.InitCollectionAgent"
            ) as mock_init_agent_class:
                mock_agent_instance = AsyncMock()
                mock_agent_instance.collection.return_value = mock_agent_response
                mock_init_agent_class.return_value = mock_agent_instance

                with patch(
                    "qines_gai_backend.modules.ai.services.is_document_accesible",
                    mock_is_accessible,
                ):
                    with patch.object(
                        service, "_build_collection_detail", new_callable=AsyncMock
                    ) as mock_build:
                        expected_detail = CollectionDetail(
                            public_collection_id="test_col01",
                            name="CAN仕様コレクション",
                            documents=[],
                            created_at=datetime(2023, 1, 1),
                            updated_at=datetime(2023, 1, 1),
                        )
                        mock_build.return_value = expected_detail

                        result = await service.create_initial_collection(
                            user_id, request
                        )

            # Assert
            assert result == expected_detail
            mock_repository.create_collection.assert_called_once()
            mock_repository.commit.assert_called_once()

        @pytest.mark.asyncio
        async def test_create_initial_collection_empty_documents(
            self, service, mock_repository
        ):
            """異常系：ドキュメントが見つからない場合を確認する"""
            # Arrange
            user_id = "test_user"
            request = ChatRequestBase(message="存在しないトピック")

            # エージェントが空のドキュメントリストを返す
            mock_agent_response = json.dumps(
                {"document_ids": [], "name": "Empty Collection"}
            )

            # Act & Assert
            with patch(
                "qines_gai_backend.modules.ai.services.InitCollectionAgent"
            ) as mock_init_agent_class:
                mock_agent_instance = AsyncMock()
                mock_agent_instance.collection.return_value = mock_agent_response
                mock_init_agent_class.return_value = mock_agent_instance

                with pytest.raises(CollectionCreationError) as exc_info:
                    await service.create_initial_collection(user_id, request)

                assert "Failed to create initial collection" in str(exc_info.value)
                mock_repository.rollback.assert_called_once()

        @pytest.mark.asyncio
        async def test_create_initial_collection_agent_failure(
            self, service, mock_repository
        ):
            """異常系：エージェント失敗時の処理を確認する"""
            # Arrange
            user_id = "test_user"
            request = ChatRequestBase(message="test")

            # Act & Assert
            with patch(
                "qines_gai_backend.modules.ai.services.InitCollectionAgent"
            ) as mock_init_agent_class:
                mock_agent_instance = AsyncMock()
                mock_agent_instance.collection.side_effect = Exception("Agent error")
                mock_init_agent_class.return_value = mock_agent_instance

                with pytest.raises(CollectionCreationError) as exc_info:
                    await service.create_initial_collection(user_id, request)

                assert "Failed to create initial collection" in str(exc_info.value)
                mock_repository.rollback.assert_called_once()

        @pytest.mark.asyncio
        async def test_create_initial_collection_rollback_on_error(
            self, service, mock_repository
        ):
            """異常系：エラー時にロールバックが呼ばれることを確認する"""
            # Arrange
            user_id = "test_user"
            request = ChatRequestBase(message="test")

            mock_repository.create_collection.side_effect = Exception("DB error")

            # Act & Assert
            with patch(
                "qines_gai_backend.modules.ai.services.InitCollectionAgent"
            ) as mock_init_agent_class:
                mock_agent_instance = AsyncMock()
                mock_agent_instance.collection.return_value = json.dumps(
                    {"document_ids": [str(uuid.uuid4())], "name": "Test"}
                )
                mock_init_agent_class.return_value = mock_agent_instance

                with patch(
                    "qines_gai_backend.modules.ai.services.is_document_accesible",
                    AsyncMock(return_value=True),
                ):
                    with pytest.raises(CollectionCreationError):
                        await service.create_initial_collection(user_id, request)

                    mock_repository.rollback.assert_called_once()

    class TestValidateStreamChatRequest:
        """validate_stream_chat_requestメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_validate_success(
            self, service, mock_repository, sample_collection, sample_conversation
        ):
            """正常系：検証が成功することを確認する"""
            # Arrange
            user_id = "test_user"
            request = ChatCompletionsRequest(
                message="test message",
                public_collection_id="test_col01",
                public_conversation_id="test_conv01",
            )

            mock_repository.get_collection_by_public_id.return_value = sample_collection
            mock_repository.get_conversation_by_public_id.return_value = (
                sample_conversation
            )

            # Act
            result = await service.validate_stream_chat_request(user_id, request)

            # Assert
            assert result is None
            mock_repository.get_collection_by_public_id.assert_called_once_with(
                "test_col01"
            )
            mock_repository.get_conversation_by_public_id.assert_called_once_with(
                "test_conv01"
            )

        @pytest.mark.asyncio
        async def test_validate_collection_not_found(self, service, mock_repository):
            """異常系：コレクションが見つからない場合を確認する"""
            # Arrange
            user_id = "test_user"
            request = ChatCompletionsRequest(
                message="test message", public_collection_id="nonexistent"
            )

            mock_repository.get_collection_by_public_id.return_value = None

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await service.validate_stream_chat_request(user_id, request)

            assert exc_info.value.status_code == 404
            assert "Collection not found" in str(exc_info.value.detail)

        @pytest.mark.asyncio
        async def test_validate_not_authorized(
            self, service, mock_repository, sample_collection
        ):
            """異常系：権限がない場合を確認する"""
            # Arrange
            user_id = "other_user"
            request = ChatCompletionsRequest(
                message="test message", public_collection_id="test_col01"
            )

            sample_collection.user_id = "owner_user"
            mock_repository.get_collection_by_public_id.return_value = sample_collection

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await service.validate_stream_chat_request(user_id, request)

            assert exc_info.value.status_code == 403
            assert "Not authorized to use this collection" in str(exc_info.value.detail)

        @pytest.mark.asyncio
        async def test_validate_conversation_not_found(
            self, service, mock_repository, sample_collection
        ):
            """異常系：会話が見つからない場合を確認する"""
            # Arrange
            user_id = "test_user"
            request = ChatCompletionsRequest(
                message="test message",
                public_collection_id="test_col01",
                public_conversation_id="nonexistent",
            )

            mock_repository.get_collection_by_public_id.return_value = sample_collection
            mock_repository.get_conversation_by_public_id.return_value = None

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await service.validate_stream_chat_request(user_id, request)

            assert exc_info.value.status_code == 404
            assert "Conversation not found" in str(exc_info.value.detail)

    class TestStreamChat:
        """stream_chatメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_stream_chat_new_conversation(
            self, service, mock_repository, sample_collection
        ):
            """正常系：新規会話でのストリーミングを確認する"""
            # Arrange
            user_id = "test_user"
            request = ChatCompletionsRequest(
                message="test message", public_collection_id="test_col01"
            )

            mock_repository.get_collection_by_public_id.return_value = sample_collection

            # _generate_and_saveとその他の依存関係のモック
            async def mock_generate():
                yield '{"type": "message", "content": "Hello"}'
                yield '{"type": "message", "content": " World"}'

            # Act
            with patch.object(
                service, "_build_collection_detail", new_callable=AsyncMock
            ) as mock_build:
                mock_collection_detail = MagicMock()
                mock_build.return_value = mock_collection_detail

                with patch(
                    "qines_gai_backend.modules.ai.services.Agent"
                ) as mock_agent_class:
                    mock_agent = AsyncMock()
                    # Agent.createはasyncメソッドなので、AsyncMockで返す
                    mock_agent_class.create = AsyncMock(return_value=mock_agent)

                    with patch.object(
                        service, "_generate_and_save", return_value=mock_generate()
                    ):
                        result_gen = service.stream_chat(user_id, request)
                        results = []
                        async for chunk in result_gen:
                            results.append(chunk)

            # Assert
            assert len(results) == 2

        @pytest.mark.asyncio
        async def test_stream_chat_existing_conversation(
            self, service, mock_repository, sample_collection, sample_conversation
        ):
            """正常系：既存会話での継続ストリーミングを確認する"""
            # Arrange
            user_id = "test_user"
            request = ChatCompletionsRequest(
                message="test message",
                public_collection_id="test_col01",
                public_conversation_id="test_conv01",
            )

            mock_repository.get_collection_by_public_id.return_value = sample_collection
            mock_repository.get_conversation_by_public_id.return_value = (
                sample_conversation
            )
            sample_conversation.artifacts = []

            # _generate_and_saveとその他の依存関係のモック
            async def mock_generate():
                yield '{"type": "message", "content": "Response"}'

            # Act
            with patch.object(
                service, "_build_collection_detail", new_callable=AsyncMock
            ) as mock_build:
                mock_collection_detail = MagicMock()
                mock_build.return_value = mock_collection_detail

                with patch(
                    "qines_gai_backend.modules.ai.services.Agent"
                ) as mock_agent_class:
                    mock_agent = AsyncMock()
                    # Agent.createはasyncメソッドなので、AsyncMockで返す
                    mock_agent_class.create = AsyncMock(return_value=mock_agent)

                    with patch.object(
                        service, "_generate_and_save", return_value=mock_generate()
                    ):
                        result_gen = service.stream_chat(user_id, request)
                        results = []
                        async for chunk in result_gen:
                            results.append(chunk)

            # Assert
            assert len(results) == 1

        @pytest.mark.asyncio
        async def test_stream_chat_error_handling(
            self, service, mock_repository, sample_collection
        ):
            """異常系：エラーハンドリングを確認する"""
            # Arrange
            user_id = "test_user"
            request = ChatCompletionsRequest(
                message="test message", public_collection_id="test_col01"
            )

            mock_repository.get_collection_by_public_id.return_value = sample_collection
            mock_repository.update_collection_used_at.side_effect = Exception(
                "Update error"
            )

            # Act
            with patch.object(
                service, "validate_stream_chat_request", new_callable=AsyncMock
            ) as mock_validate:
                mock_validate.return_value = (sample_collection, None)

                # エラーが発生するが、generatorは正常に動作する
                result_gen = service.stream_chat(user_id, request)

                # エラーが発生してもgeneratorは開始できる
                assert result_gen is not None

        @pytest.mark.asyncio
        async def test_stream_chat_with_existing_conversation_and_messages(
            self, service, mock_repository, sample_collection, sample_conversation
        ):
            """正常系：既存会話のメッセージ履歴を含むstream_chatを確認する"""
            # Arrange: sample_conversationにメッセージ履歴を追加
            from qines_gai_backend.schemas.schema import T_Message

            user_message = MagicMock(spec=T_Message)
            user_message.sender_type = "user"
            user_message.content = "前の質問"
            user_message.metadata_info = {}

            ai_message = MagicMock(spec=T_Message)
            ai_message.sender_type = "assistant"
            ai_message.content = "前の回答"
            ai_message.metadata_info = {
                "version": 1,
                "contexts": [],
                "recommended_documents": [],
                "generated_artifacts": [],
            }

            sample_conversation.messages = [user_message, ai_message]
            sample_conversation.artifacts = []

            user_id = "test_user"
            request = ChatCompletionsRequest(
                message="新しい質問",
                public_collection_id="test_col01",
                public_conversation_id="test_conv01",
            )

            mock_repository.get_collection_by_public_id.return_value = sample_collection
            mock_repository.get_conversation_by_public_id.return_value = (
                sample_conversation
            )

            # _generate_and_saveとその他の依存関係のモック
            async def mock_generate():
                yield '{"type": "message", "content": "新しい回答"}'

            # Act
            with patch.object(
                service, "_build_collection_detail", new_callable=AsyncMock
            ) as mock_build:
                mock_collection_detail = MagicMock()
                mock_build.return_value = mock_collection_detail

                with patch(
                    "qines_gai_backend.modules.ai.services.Agent"
                ) as mock_agent_class:
                    mock_agent = AsyncMock()
                    mock_agent_class.create = AsyncMock(return_value=mock_agent)

                    with patch.object(
                        service, "_generate_and_save", return_value=mock_generate()
                    ):
                        result_gen = service.stream_chat(user_id, request)
                        results = []
                        async for chunk in result_gen:
                            results.append(chunk)

            # Assert
            assert len(results) == 1
            # メッセージ履歴が正しく処理されたことを確認
            mock_repository.get_conversation_by_public_id.assert_called_once_with(
                "test_conv01"
            )

        @pytest.mark.asyncio
        async def test_stream_chat_exception_in_stream(
            self, service, mock_repository, sample_collection
        ):
            """異常系：stream_chat内で例外が発生した場合のエラーハンドリングを確認する"""
            # Arrange
            user_id = "test_user"
            request = ChatCompletionsRequest(
                message="test message", public_collection_id="test_col01"
            )

            mock_repository.get_collection_by_public_id.return_value = sample_collection

            # Act
            with patch.object(
                service, "_build_collection_detail", new_callable=AsyncMock
            ) as mock_build:
                # _build_collection_detailで例外を発生させる
                mock_build.side_effect = Exception("Build error")

                result_gen = service.stream_chat(user_id, request)
                results = []
                async for chunk in result_gen:
                    results.append(chunk)

            # Assert
            # エラーメッセージが返されることを確認
            assert len(results) == 1
            assert '{"error": "Internal Server Error"}' in results[0]

    class TestBuildCollectionDetail:
        """_build_collection_detailメソッドのテストクラス（privateメソッド）"""

        @pytest.mark.asyncio
        async def test_build_collection_detail_success(
            self, service, mock_repository, sample_collection
        ):
            """正常系：コレクション詳細構築が成功することを確認する"""
            # Arrange
            sample_collection.collection_documents = []

            # Act
            with patch(
                "qines_gai_backend.modules.ai.services.convert_datetime_utc_to_jst"
            ) as mock_convert:
                mock_convert.side_effect = lambda x: x
                result = await service._build_collection_detail(sample_collection)

            # Assert
            assert result.public_collection_id == "test_col01"
            assert result.name == "Test AI Collection"
            assert result.documents == []

        @pytest.mark.asyncio
        async def test_build_collection_detail_empty_documents(
            self, service, sample_collection
        ):
            """正常系：ドキュメントなしのコレクション詳細構築を確認する"""
            # Arrange
            sample_collection.collection_documents = []

            # Act
            with patch(
                "qines_gai_backend.modules.ai.services.convert_datetime_utc_to_jst"
            ) as mock_convert:
                mock_convert.side_effect = lambda x: x
                result = await service._build_collection_detail(sample_collection)

            # Assert
            assert len(result.documents) == 0

    class TestGenerateTitle:
        """_generate_titleメソッドのテストクラス（privateメソッド）"""

        @pytest.mark.asyncio
        async def test_generate_title_success(self, service):
            """正常系：タイトル生成が成功することを確認する"""
            # Arrange
            user_message = "CANについて教えて"
            ai_response = "CANはController Area Networkの略です"

            # Act
            with patch(
                "qines_gai_backend.modules.ai.services.LLMWrapper"
            ) as mock_wrapper:
                mock_llm = AsyncMock()
                # services.py:458-459でdictの場合はtitleキーを取得する
                mock_llm.ainvoke.return_value = {"title": "CANについて"}
                mock_wrapper.return_value.get_structured_llm.return_value = mock_llm

                result = await service._generate_title(user_message, ai_response)

            # Assert
            assert result == "CANについて"

        @pytest.mark.asyncio
        async def test_generate_title_llm_failure(self, service):
            """異常系：LLM失敗時にデフォルト値を返すことを確認する"""
            # Arrange
            user_message = "test"
            ai_response = "response"

            # Act
            with patch(
                "qines_gai_backend.modules.ai.services.LLMWrapper"
            ) as mock_wrapper:
                mock_llm = AsyncMock()
                mock_llm.ainvoke.side_effect = Exception("LLM error")
                mock_wrapper.return_value.get_structured_llm.return_value = mock_llm

                result = await service._generate_title(user_message, ai_response)

            # Assert
            assert result == "なし"

        @pytest.mark.asyncio
        async def test_generate_title_returns_list(self, service):
            """正常系：listを返す場合の先頭要素取得を確認する"""
            # Arrange
            user_message = "CANについて教えて"
            ai_response = "CANはController Area Networkの略です"

            # Act
            with patch(
                "qines_gai_backend.modules.ai.services.LLMWrapper"
            ) as mock_wrapper:
                mock_llm = AsyncMock()
                # services.py:456-457でlistの場合は[0]を取得する
                mock_llm.ainvoke.return_value = ["CANについて", "別のタイトル"]
                mock_wrapper.return_value.get_structured_llm.return_value = mock_llm

                result = await service._generate_title(user_message, ai_response)

            # Assert
            assert result == "CANについて"

        @pytest.mark.asyncio
        async def test_generate_title_returns_other_type(self, service):
            """異常系：dict/list以外を返す場合のデフォルト値を確認する"""
            # Arrange
            user_message = "test"
            ai_response = "response"

            # Act
            with patch(
                "qines_gai_backend.modules.ai.services.LLMWrapper"
            ) as mock_wrapper:
                mock_llm = AsyncMock()
                # services.py:460-461でその他の型の場合は"なし"を返す
                mock_llm.ainvoke.return_value = "unexpected string"
                mock_wrapper.return_value.get_structured_llm.return_value = mock_llm

                result = await service._generate_title(user_message, ai_response)

            # Assert
            assert result == "なし"
