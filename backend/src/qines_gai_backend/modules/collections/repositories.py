from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.schemas.schema import (
    T_Collection,
    T_CollectionDocument,
    T_Conversation,
)
from qines_gai_backend.shared.exceptions import (
    CollectionNotFoundError,
    NotAuthorizedCollectionError,
)

logger = get_logger(__name__)


class CollectionRepository:
    """コレクション関連のデータアクセス層"""

    def __init__(self, session: AsyncSession):
        """CollectionRepositoryを初期化する。

        Args:
            session (AsyncSession): SQLAlchemyの非同期セッション
        """
        self.session = session

    @log_function_start_end
    async def create_collection(
        self, user_id: str, name: str, document_uuids: list[UUID]
    ) -> T_Collection:
        """新しいコレクションを作成し、指定されたドキュメントを関連付ける。

        Args:
            user_id (str): コレクションを作成するユーザーのID
            name (str): コレクションの名前
            document_uuids (list[UUID]): コレクションに含めるドキュメントのUUIDリスト

        Returns:
            T_Collection: 作成されたコレクションのデータベースレコード
        """
        new_collection = T_Collection(user_id=user_id, name=name)
        self.session.add(new_collection)
        await self.session.flush()

        for index, doc_uuid in enumerate(document_uuids):
            new_collection_doc = T_CollectionDocument(
                collection_id=new_collection.collection_id,
                document_id=doc_uuid,
                position=index + 1,
            )
            self.session.add(new_collection_doc)

        await self.session.flush()
        return new_collection

    @log_function_start_end
    async def get_collections_by_user(
        self, user_id: str, offset: int = 0, limit: int = 100
    ) -> tuple[list[T_Collection], int]:
        """指定されたユーザーIDに紐づくコレクション一覧を最終使用日時順で取得する。

        Args:
            user_id (str): コレクションを取得したいユーザーID
            offset (int, optional): ページネーションの開始位置。デフォルトは0
            limit (int, optional): 取得する最大件数。デフォルトは100

        Returns:
            tuple[list[T_Collection], int]: コレクションリストと総件数のタプル
        """
        query = (
            select(T_Collection)
            .filter(T_Collection.user_id == user_id)
            .order_by(T_Collection.used_at.desc())
        )

        # 総件数取得
        total_result = await self.session.execute(query)
        total = len(total_result.unique().scalars().all())

        # ページネーション適用
        result = await self.session.execute(query.offset(offset).limit(limit))
        collections = result.unique().scalars().all()

        return collections, total

    @log_function_start_end
    async def get_collection_by_public_id(
        self, public_collection_id: str, user_id: Optional[str] = None
    ) -> T_Collection:
        """公開コレクションIDでコレクションを取得し、権限チェックを実行する。

        Args:
            public_collection_id (str): 取得したいコレクションの公開ID
            user_id (Optional[str], optional): 権限チェック用のユーザーID。デフォルトはNone

        Returns:
            T_Collection: 取得されたコレクションのデータベースレコード

        Raises:
            CollectionNotFoundError: 指定されたコレクションが存在しない場合
            NotAuthorizedCollectionError: ユーザーIDが指定された場合で、権限がない場合
        """
        query = select(T_Collection).filter_by(
            public_collection_id=public_collection_id
        )
        result = await self.session.execute(query)
        collection = result.scalar()

        if not collection:
            raise CollectionNotFoundError()

        if user_id and collection.user_id != user_id:
            raise NotAuthorizedCollectionError()

        return collection

    @log_function_start_end
    async def get_collection_with_documents(
        self, public_collection_id: str, user_id: Optional[str] = None
    ) -> tuple[T_Collection, list[T_CollectionDocument]]:
        """コレクションとそれに紐づくドキュメント情報を一括取得する。

        Args:
            public_collection_id (str): 取得したいコレクションの公開ID
            user_id (Optional[str], optional): 権限チェック用のユーザーID。デフォルトはNone

        Returns:
            tuple[T_Collection, list[T_CollectionDocument]]: コレクションとドキュメント関連情報のタプル

        Note:
            ドキュメント情報はポジション順でソートされ、eager loadingが適用される
        """
        collection = await self.get_collection_by_public_id(
            public_collection_id, user_id
        )

        query = (
            select(T_CollectionDocument)
            .filter_by(collection_id=collection.collection_id)
            .order_by(T_CollectionDocument.position)
            .options(selectinload(T_CollectionDocument.document))
        )
        result = await self.session.execute(query)
        collection_documents = result.unique().scalars().all()

        # eager loadingを確実にするため、ここでdocumentアクセスを強制
        for collection_doc in collection_documents:
            # documentの属性に一度アクセスしてロードを完了させる
            _ = collection_doc.document.document_id
            _ = collection_doc.document.file_name
            _ = collection_doc.document.file_path
            _ = collection_doc.document.metadata_info
            _ = collection_doc.document.file_type

        return collection, collection_documents

    @log_function_start_end
    async def update_collection(
        self,
        collection_id: UUID,
        name: str,
        document_uuids: list[UUID],
    ) -> None:
        """既存のコレクションの名前と含まれるドキュメントを更新する。

        Args:
            collection_id (UUID): 更新対象のコレクションID
            name (str): 新しいコレクション名
            document_uuids (list[UUID]): 新しいドキュメントUUIDリスト

        Note:
            指定されたドキュメントリストに含まれないドキュメントは削除され、
            新しいドキュメントは追加される。既存のドキュメントの順序は更新される。
        """
        # コレクション名を更新
        update_stmt = (
            update(T_Collection)
            .where(T_Collection.collection_id == collection_id)
            .values(name=name)
        )
        await self.session.execute(update_stmt)

        # 既存のコレクションドキュメントを取得
        query = select(T_CollectionDocument).filter_by(collection_id=collection_id)
        result = await self.session.execute(query)
        existing_collection_docs = result.unique().scalars().all()

        # 削除するコレクションドキュメントを特定
        collection_docs_to_delete = [
            collection_doc
            for collection_doc in existing_collection_docs
            if collection_doc.document_id not in document_uuids
        ]

        # 不要なコレクションドキュメントを削除
        for collection_doc in collection_docs_to_delete:
            await self.session.delete(collection_doc)

        # コレクションドキュメントを作成または更新
        for index, doc_uuid in enumerate(document_uuids):
            existing_collection_doc = next(
                (
                    collection_doc
                    for collection_doc in existing_collection_docs
                    if collection_doc.document_id == doc_uuid
                ),
                None,
            )

            if existing_collection_doc:
                # 既存のドキュメントの位置を更新
                update_stmt = (
                    update(T_CollectionDocument)
                    .where(T_CollectionDocument.collection_id == collection_id)
                    .where(T_CollectionDocument.document_id == doc_uuid)
                    .values(position=index + 1)
                )
                await self.session.execute(update_stmt)
            else:
                # 新規コレクションドキュメントを作成
                new_collection_doc = T_CollectionDocument(
                    collection_id=collection_id,
                    document_id=doc_uuid,
                    position=index + 1,
                )
                self.session.add(new_collection_doc)

        await self.session.flush()

    @log_function_start_end
    async def get_conversations_by_collection(
        self, collection_id: UUID, user_id: str
    ) -> list[T_Conversation]:
        """指定されたコレクションに紐づく会話履歴一覧を更新日時順で取得する。

        Args:
            collection_id (UUID): 対象のコレクションID
            user_id (str): 会話履歴の所有者となるユーザーID

        Returns:
            list[T_Conversation]: 該当する会話履歴のリスト（削除済みは除外）
        """
        query = (
            select(T_Conversation)
            .where(
                and_(
                    T_Conversation.user_id == user_id,
                    T_Conversation.collection_id == collection_id,
                    T_Conversation.is_deleted.is_(False),
                )
            )
            .order_by(T_Conversation.updated_at.desc())
        )

        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def commit(self) -> None:
        """データベーストランザクションをコミットし、変更を確定する。

        Raises:
            データベースエラーが発生した場合の例外
        """
        await self.session.commit()

    async def rollback(self) -> None:
        """データベーストランザクションをロールバックし、変更を破棄する。

        Note:
            エラー発生時や例外ハンドリングで使用される
        """
        await self.session.rollback()
