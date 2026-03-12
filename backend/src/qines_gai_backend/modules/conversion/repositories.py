"""Update module data access layer

成果物更新処理に関するデータアクセス層を提供します。
データベース操作、MeilSearch連携、トランザクション管理を担当します。

主な機能:
- 成果物データの取得
- ドキュメントの作成・更新・削除・復元
- コレクションドキュメントの参照更新
- トランザクションのコミット・ロールバック
"""

import uuid

from meilisearch_python_sdk import AsyncClient
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.schemas.schema import T_Collection, T_CollectionDocument
from qines_gai_backend.shared.exceptions import (
    CollectionNotFoundError,
    DocumentUpdateError,
)

logger = get_logger(__name__)


class ConversionRepository:
    """ドキュメント更新関連のデータアクセス層。

    AIによって生成された成果物をドキュメントとして登録・更新する際の
    データベース操作を提供します。

    主な責任範囲:
    - 成果物データの取得と検証
    - ドキュメントレコードの作成・更新・削除・復元
    - コレクション内ドキュメント参照の更新
    - データベーストランザクションの管理
    - MeilSearchクライアントへのアクセス提供

    トランザクション管理:
    すべてのデータベース操作はAsyncSessionで管理され、
    明示的なコミットまたはロールバックが必要です。
    """

    def __init__(self, session: AsyncSession, meili_client: AsyncClient) -> None:
        """UpdateRepositoryを初期化する。

        Args:
            session (AsyncSession): データベース操作用のSQLAlchemy非同期セッション
            meili_client (AsyncClient): 検索インデックス操作用のMeilSearchクライアント
        """
        self.session = session
        self.meili_client = meili_client
        self._logger = logger

    async def commit(self) -> None:
        """データベーストランザクションをコミットする。

        現在のセッションで実行されたすべての変更をデータベースに確定します。
        コミット後、トランザクションは終了し、変更は復元できなくなります。

        Raises:
            DocumentUpdateError: コミット処理中にエラーが発生した場合
        """
        try:
            self._logger.debug("Committing database transaction")
            await self.session.commit()
            self._logger.debug("Database transaction committed successfully")
        except SQLAlchemyError as e:
            error_msg = f"Failed to commit database transaction: {str(e)}"
            self._logger.error(error_msg)
            raise DocumentUpdateError(error_msg) from e

    async def rollback(self) -> None:
        """データベーストランザクションをロールバックする。

        現在のセッションで実行されたすべての変更を破棄し、
        トランザクション開始時の状態に戻します。
        エラー時の復旧処理や予期しない事態の対応に使用します。

        Raises:
            DocumentUpdateError: ロールバック処理中にエラーが発生した場合
        """
        try:
            self._logger.debug("Rolling back database transaction")
            await self.session.rollback()
            self._logger.debug("Database transaction rolled back successfully")
        except SQLAlchemyError as e:
            error_msg = f"Failed to rollback database transaction: {str(e)}"
            self._logger.error(error_msg)
            raise DocumentUpdateError(error_msg) from e

    @log_function_start_end
    async def add_document_to_collection(
        self, public_collection_id: str, document_id: str, add_flag: bool = False
    ) -> None:
        """コレクションにドキュメントを追加する。

        指定されたコレクションにドキュメントを追加します。
        既に同じドキュメントがある場合は重複は作成されません。

        Args:
            public_collection_id (str): コレクションの公開コレクションID
            document_id (str): ドキュメントの一意識別子

        Raises:
            DocumentUpdateError: コレクションドキュメントの作成中にエラーが発生した場合
        """
        try:
            # public_collection_idからcollection_idを取得する
            select_stmt = select(T_Collection).filter_by(
                public_collection_id=public_collection_id,
            )
            result = await self.session.execute(select_stmt)
            collection = result.scalars().first()

            if not collection:
                raise CollectionNotFoundError()

            collection_id = str(collection.collection_id)

            self._logger.debug(
                f"Adding document {document_id} to collection {collection_id}"
            )

            # 上書きの場合はコレクションドキュメントの存在確認を行い、処理終了
            # ただし、存在しなかった場合はコレクションドキュメントを生成する。
            if not add_flag:
                # 既存のコレクションドキュメントを確認
                select_stmt = select(T_CollectionDocument).filter_by(
                    collection_id=uuid.UUID(collection_id),
                    document_id=uuid.UUID(document_id),
                )
                result = await self.session.execute(select_stmt)
                existing = result.scalars().first()

                if existing:
                    self._logger.debug(
                        f"Document {document_id} already exists in collection {collection_id}"
                    )
                    return

            # 順番を確認するため、コレクションIDでコレクションドキュメントを検索
            count_query = (
                select(func.count())
                .select_from(T_CollectionDocument)
                .filter_by(collection_id=uuid.UUID(collection_id))
            )
            count_result = await self.session.execute(count_query)
            total_count = count_result.scalar() or 0

            # 新しいコレクションドキュメントを作成
            collection_document = T_CollectionDocument(
                collection_id=uuid.UUID(collection_id),
                document_id=uuid.UUID(document_id),
                position=total_count + 1,
            )

            self.session.add(collection_document)
            await self.session.flush()

            self._logger.debug(
                f"Successfully added document {document_id} to collection {collection_id}"
            )

        except ValueError as e:
            # UUID変換エラー
            error_msg = f"Invalid UUID format: {str(e)}"
            self._logger.error(error_msg)
            raise DocumentUpdateError(error_msg) from e
        except SQLAlchemyError as e:
            error_msg = f"Failed to add document to collection: {str(e)}"
            self._logger.error(error_msg)
            raise DocumentUpdateError(error_msg) from e
