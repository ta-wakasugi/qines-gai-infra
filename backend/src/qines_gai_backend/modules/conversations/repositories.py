from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from qines_gai_backend.schemas.schema import T_Artifact, T_Conversation, T_Message


class ConversationRepository:
    """会話履歴データアクセス"""

    def __init__(self, session: AsyncSession):
        """ConversationRepositoryを初期化する。

        Args:
            session (AsyncSession): SQLAlchemyの非同期セッション
        """
        self.session = session

    async def get_conversation_by_public_id(
        self, public_conversation_id: str
    ) -> Optional[T_Conversation]:
        """公開会話履歴IDで会話履歴を取得する。

        Args:
            public_conversation_id (str): 取得したい会話履歴の公開ID

        Returns:
            Optional[T_Conversation]: 該当する会話履歴レコード。存在しない場合はNone
        """

        stmt = select(T_Conversation).where(
            and_(
                T_Conversation.public_conversation_id == public_conversation_id,
                T_Conversation.is_deleted.is_(False),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_message_by_id(self, conversation_id: str) -> Optional[T_Message]:
        """会話履歴IDに紐づくメッセージ一覧を作成日時順で取得する。

        Args:
            conversation_id (str): 対象の会話履歴ID

        Returns:
            Optional[T_Message]: 該当する会話履歴に紐づくメッセージ一覧。存在しない場合は空のリスト
        """

        stmt = (
            select(T_Message)
            .where(
                and_(
                    T_Message.conversation_id == conversation_id,
                )
            )
            .order_by(T_Message.created_at)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_artifact_by_id(self, conversation_id: str) -> Optional[T_Artifact]:
        """会話履歴IDに紐づく成果物一覧を作成日時順で取得する。

        Args:
            conversation_id (str): 対象の会話履歴ID

        Returns:
            Optional[T_Artifact]: 該当する会話履歴に紐づく成果物一覧。存在しない場合は空のリスト
        """

        select_stmt = (
            select(T_Artifact)
            .where(
                and_(
                    T_Artifact.conversation_id == conversation_id,
                )
            )
            .order_by(T_Artifact.created_at)
        )
        result = await self.session.execute(select_stmt)
        return result.scalars().all()
