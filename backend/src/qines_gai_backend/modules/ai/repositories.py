from typing import List, Optional
from uuid import UUID, uuid4

import nanoid
from meilisearch_python_sdk import AsyncClient
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.schemas.schema import (
    T_Artifact,
    T_Collection,
    T_CollectionDocument,
    T_Conversation,
    T_Message,
)

logger = get_logger(__name__)


class AIRepository:
    """AI関連のデータアクセス層

    AI機能に必要なデータベース操作（コレクション、会話、メッセージ、アーティファクト）
    とMeilSearchクライアントへのアクセスを提供します。
    """

    def __init__(self, session: AsyncSession, meili_client: AsyncClient):
        """AIRepositoryを初期化する

        Args:
            session (AsyncSession): SQLAlchemyの非同期セッション
            meili_client (AsyncClient): MeilSearchクライアント
        """
        self.session = session
        self.meili_client = meili_client

    @log_function_start_end
    async def create_collection(
        self,
        user_id: str,
        collection_name: str,
        document_ids: List[str],
    ) -> T_Collection:
        """新しいコレクションを作成する

        指定されたドキュメントIDリストを含む新しいコレクションを作成し、
        collection_documentsテーブルにも関連レコードを追加します。

        Args:
            user_id (str): コレクションを作成するユーザーID
            collection_name (str): コレクション名
            document_ids (List[str]): コレクションに含めるドキュメントIDのリスト

        Returns:
            T_Collection: 作成されたコレクションオブジェクト
        """
        new_collection_id = str(uuid4())
        new_public_collection_id = nanoid.generate(size=11)

        # collectionsテーブルの編集
        new_collection = T_Collection(
            collection_id=new_collection_id,
            public_collection_id=new_public_collection_id,
            user_id=user_id,
            name=collection_name,
        )
        self.session.add(new_collection)

        # collection_documentsテーブルの編集
        for position, document_id in enumerate(document_ids):
            new_collection_doc = T_CollectionDocument(
                collection_id=UUID(new_collection_id),
                document_id=UUID(document_id),
                position=position + 1,
            )
            self.session.add(new_collection_doc)

        await self.session.flush()

        # collection_documentsを明示的にロードする
        await self.session.refresh(new_collection)

        return new_collection

    @log_function_start_end
    async def get_collection_by_public_id(
        self, public_collection_id: str, user_id: Optional[str] = None
    ) -> Optional[T_Collection]:
        """公開コレクションIDでコレクションを取得する

        公開コレクションIDに基づいてコレクションを検索します。
        user_idが指定された場合、所有者チェックを行います。

        Args:
            public_collection_id (str): 公開コレクションID
            user_id (Optional[str]): ユーザーID（所有者チェック用）

        Returns:
            Optional[T_Collection]: 見つかったコレクション、または None
        """
        stmt = (
            select(T_Collection)
            .filter_by(public_collection_id=public_collection_id)
            .options(selectinload(T_Collection.collection_documents))
        )

        result = await self.session.execute(stmt)
        collection_record = result.scalars().first()

        if collection_record and user_id and user_id != collection_record.user_id:
            return None

        return collection_record

    @log_function_start_end
    async def get_conversation_by_public_id(
        self, public_conversation_id: str
    ) -> Optional[T_Conversation]:
        """公開会話IDで会話履歴を取得する

        公開会話IDに基づいて会話履歴を検索し、関連するメッセージと
        アーティファクトも一緒に取得します。

        Args:
            public_conversation_id (str): 公開会話ID

        Returns:
            Optional[T_Conversation]: 見つかった会話オブジェクト、または None
        """
        stmt = (
            select(T_Conversation)
            .options(
                contains_eager(T_Conversation.messages).options(
                    selectinload(T_Message.artifacts)
                ),
            )
            .outerjoin(T_Conversation.messages)
            .filter(T_Conversation.is_deleted.is_(False))
            .filter(T_Conversation.public_conversation_id == public_conversation_id)
            .order_by(T_Message.created_at.asc())
        )

        result = await self.session.execute(stmt)
        return result.scalar()

    @log_function_start_end
    async def create_conversation(
        self,
        public_conversation_id: str,
        user_id: str,
        collection_id: str,
        title: str,
    ) -> T_Conversation:
        """新しい会話を作成する

        指定されたパラメータで新しい会話レコードを作成します。

        Args:
            public_conversation_id (str): 公開会話ID
            user_id (str): ユーザーID
            collection_id (str): コレクションID
            title (str): 会話のタイトル

        Returns:
            T_Conversation: 作成された会話オブジェクト
        """
        conversation_record = T_Conversation(
            public_conversation_id=public_conversation_id,
            user_id=user_id,
            collection_id=collection_id,
            title=title,
        )
        self.session.add(conversation_record)
        await self.session.flush()
        return conversation_record

    @log_function_start_end
    async def update_conversation(self, conversation: T_Conversation) -> T_Conversation:
        """会話を更新する

        既存の会話オブジェクトの更新時刻を現在時刻に設定して更新します。

        Args:
            conversation (T_Conversation): 更新する会話オブジェクト

        Returns:
            T_Conversation: 更新された会話オブジェクト
        """
        conversation.updated_at = func.now()
        return await self.session.merge(conversation)

    @log_function_start_end
    async def create_message(
        self,
        conversation_id: str,
        sender_type: str,
        content: str,
        metadata_info: dict,
    ) -> T_Message:
        """新しいメッセージを作成する

        指定された会話に新しいメッセージを追加します。

        Args:
            conversation_id (str): 会話ID
            sender_type (str): 送信者タイプ（'user' または 'ai'）
            content (str): メッセージ内容
            metadata_info (dict): メッセージのメタデータ情報

        Returns:
            T_Message: 作成されたメッセージオブジェクト
        """
        message = T_Message(
            conversation_id=conversation_id,
            sender_type=sender_type,
            content=content,
            metadata_info=metadata_info,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    @log_function_start_end
    async def create_artifact(
        self,
        artifact_id: str,
        conversation_id: str,
        message_id: str,
        title: str,
        version: int,
        content: str,
    ) -> T_Artifact:
        """新しいアーティファクトを作成する

        AIによって生成されたアーティファクト（コード、ドキュメントなど）を
        データベースに保存します。

        Args:
            artifact_id (str): アーティファクトID
            conversation_id (str): 会話ID
            message_id (str): メッセージID
            title (str): アーティファクトのタイトル
            version (int): バージョン番号
            content (str): アーティファクトの内容

        Returns:
            T_Artifact: 作成されたアーティファクトオブジェクト
        """
        artifact = T_Artifact(
            artifact_id=artifact_id,
            conversation_id=conversation_id,
            message_id=message_id,
            title=title,
            version=version,
            content=content,
        )
        self.session.add(artifact)
        await self.session.flush()
        return artifact

    @log_function_start_end
    async def update_collection_used_at(self, collection_id: str) -> None:
        """コレクションの使用時刻を更新する

        指定されたコレクションのused_atフィールドを現在時刻に更新します。

        Args:
            collection_id (str): 更新するコレクションのID
        """
        stmt = (
            update(T_Collection)
            .where(T_Collection.collection_id == collection_id)
            .values(used_at=func.now())
        )
        await self.session.execute(stmt)

    async def commit(self) -> None:
        """トランザクションをコミットする

        現在のデータベーストランザクションをコミットして変更を確定します。
        """
        await self.session.commit()

    async def rollback(self) -> None:
        """トランザクションをロールバックする

        現在のデータベーストランザクションをロールバックして変更を取り消します。
        """
        await self.session.rollback()
