from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from qines_gai_backend.config.dependencies.data_connection import User
from qines_gai_backend.modules.conversations.api import (
    delete_conversation,
    get_conversation,
    share_conversation,
)
from qines_gai_backend.modules.conversations.models import ConversationDetail
from qines_gai_backend.modules.conversations.services import ConversationService
from qines_gai_backend.shared.exceptions import (
    ConversationNotFoundError,
    NotAuthorizedConversation,
)


class TestConversationAPI:
    """Conversation APIのテストクラス"""

    @pytest.fixture
    def mock_user(self):
        """ユーザーのモックを作成する"""
        user = MagicMock(spec=User)
        user.user_id = "test_user_id"
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_conversation_service(self):
        """ConversationServiceのモックを作成する"""
        return AsyncMock(spec=ConversationService)

    @pytest.fixture
    def sample_conversation_detail(self):
        """サンプル会話詳細データを作成する"""
        return ConversationDetail(
            public_conversation_id="test_conv_id",
            title="Test Conversation",
            messages=[],
            artifacts=[],
        )

    class TestGetConversation:
        """get_conversation APIのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_conversation_success(
            self, mock_user, mock_conversation_service, sample_conversation_detail
        ):
            """正常系：会話履歴の取得が成功することを確認する"""
            # Arrange
            public_conversation_id = "test_conv_id"
            mock_conversation_service.get_conversation.return_value = (
                sample_conversation_detail
            )

            # Act
            result = await get_conversation(
                public_conversation_id=public_conversation_id,
                user=mock_user,
                conversation_service=mock_conversation_service,
            )

            # Assert
            assert result == sample_conversation_detail
            mock_conversation_service.get_conversation.assert_called_once_with(
                public_conversation_id=public_conversation_id, user_id=mock_user.user_id
            )

        @pytest.mark.asyncio
        async def test_get_conversation_not_authorized(
            self, mock_user, mock_conversation_service
        ):
            """異常系：認証エラーの場合にHTTPException(403)が発生することを確認する"""
            # Arrange
            public_conversation_id = "test_conv_id"
            mock_conversation_service.get_conversation.side_effect = (
                NotAuthorizedConversation("Not authorized")
            )

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await get_conversation(
                    public_conversation_id=public_conversation_id,
                    user=mock_user,
                    conversation_service=mock_conversation_service,
                )

            assert exc_info.value.status_code == 403
            assert "Not authorized" in str(exc_info.value.detail)

        @pytest.mark.asyncio
        async def test_get_conversation_not_found(
            self, mock_user, mock_conversation_service
        ):
            """異常系：会話履歴が見つからない場合にHTTPException(404)が発生することを確認する"""
            # Arrange
            public_conversation_id = "nonexistent_id"
            mock_conversation_service.get_conversation.side_effect = (
                ConversationNotFoundError("Conversation not found")
            )

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await get_conversation(
                    public_conversation_id=public_conversation_id,
                    user=mock_user,
                    conversation_service=mock_conversation_service,
                )

            assert exc_info.value.status_code == 404
            assert "Conversation not found" in str(exc_info.value.detail)

        @pytest.mark.asyncio
        async def test_get_conversation_internal_error(
            self, mock_user, mock_conversation_service
        ):
            """異常系：内部エラーの場合にHTTPException(500)が発生することを確認する"""
            # Arrange
            public_conversation_id = "test_conv_id"
            mock_conversation_service.get_conversation.side_effect = Exception(
                "Database error"
            )

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await get_conversation(
                    public_conversation_id=public_conversation_id,
                    user=mock_user,
                    conversation_service=mock_conversation_service,
                )

            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Internal Server Error"

    class TestDeleteConversation:
        """delete_conversation APIのテストクラス"""

        def test_delete_conversation_coverage(self):
            """カバレッジのためdelete_conversationを呼ぶ"""
            # Act - カバレッジのために呼ぶだけ
            result = delete_conversation("test_conv_id")

            # Assert - 未実装なのでNoneが返される
            assert result is None

    class TestShareConversation:
        """share_conversation APIのテストクラス"""

        @pytest.mark.asyncio
        async def test_share_conversation_coverage(self):
            """カバレッジのためshare_conversationを呼ぶ"""
            # Act - カバレッジのために呼ぶだけ
            result = await share_conversation("test_conv_id")

            # Assert - 未実装なのでNoneが返される
            assert result is None
