from fastapi import Body, Path

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.shared.exceptions import (
    ConversationNotFoundError,
    NotAuthorizedConversation,
)

from .models import (
    Artifact,
    ConversationDetail,
    Message,
    MessageMetadata,
)
from .repositories import ConversationRepository

logger = get_logger(__name__)


class ConversationService:
    """会話履歴 ビジネスロジック サービス"""

    def __init__(self, repository: ConversationRepository):
        """ConversationServiceを初期化する。

        Args:
            repository (ConversationRepository): 会話履歴データアクセス用リポジトリ
        """
        self.repository = repository

    @log_function_start_end
    async def get_conversation(
        self,
        public_conversation_id: str,
        user_id: str,
    ) -> ConversationDetail:
        """
        指定された会話履歴の公開IDの詳細を取得します。

        Args:
            public_conversation_id (str): 会話履歴の公開ID。パスパラメータから取得する。
            user_id: 認証済みユーザーID。

        Returns:
            conversation_detail (CoversationDetail): 会話履歴の詳細情報。

        Raises:
            NotAuthorizedConversation: ログインユーザーが会話履歴の所有者でない場合。
            ConversationNotFoundError: 指定された会話履歴の公開IDが存在しない場合。
        """
        # 1. 会話履歴の公開IDと同じpublic_conversation_idをもつ会話履歴を見つける
        conversation = await self.repository.get_conversation_by_public_id(
            public_conversation_id
        )

        # 2. エラーハンドリングを行う
        if not conversation:
            logger.error("Conversation not found")
            raise ConversationNotFoundError()

        if conversation.user_id != user_id:
            logger.error("Not authorized to access this conversation")
            raise NotAuthorizedConversation()

        # 3. 会話履歴に基づく会話履歴の詳細を取得する
        # 3-1 messageテーブルから会話履歴IDに紐づくメッセージを取得する
        message_list = await self.repository.get_message_by_id(
            conversation.conversation_id
        )

        # 3-2 artifactsテーブルから会話履歴に紐づく成果物を取得する
        artifact_list = await self.repository.get_artifact_by_id(
            conversation.conversation_id
        )

        # 4. レスポンスデータを構築する
        # 4-1 レスポンスデータ内のmessagesフィールドを構築する
        messages = []
        for message in message_list:
            # metadataフィールドの構築
            metadata = MessageMetadata.from_db(message)

            # messagesフィールドの構築
            if message.sender_type == "ai":
                sender_type = "assistant"
            else:
                sender_type = "user"

            messages.append(
                Message(role=sender_type, content=message.content, metadata=metadata)
            )

        # 4-2 レスポンスデータ内のartifactsフィールドを構築する。
        artifacts = []
        for artifact in artifact_list:
            artifacts.append(Artifact.from_db(artifact))

        # 4-3 レスポンスデータ全体を構築する
        conversation_detail = ConversationDetail(
            public_conversation_id=conversation.public_conversation_id,
            title=conversation.title,
            messages=messages,
            artifacts=artifacts,
        )

        return conversation_detail

    def delete_conversation(
        public_conversation_id: str = Path(
            ..., description="会話履歴の公開ID", example="Zf2k6A6R5h2"
        ),
    ):
        """指定された公開会話履歴IDの会話履歴を論理削除する。

        Args:
            public_conversation_id (str): 削除したい会話履歴の公開ID

        Note:
            現在未実装。将来の機能拡張用のプレースホルダー
        """
        return

    async def share_conversation(
        public_conversation_id: str = Body(
            ..., description="共有したい会話履歴のID", example="V1StGXR8_Z5", embed=True
        ),
    ):
        """指定された公開会話履歴IDの会話履歴を共有可能な状態にする。

        Args:
            public_conversation_id (str): 共有したい会話履歴の公開ID

        Note:
            現在未実装。将来の機能拡張用のプレースホルダー
        """
        return
