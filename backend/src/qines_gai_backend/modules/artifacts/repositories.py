"""Artifacts module data access layer"""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.schemas.schema import T_Artifact

logger = get_logger(__name__)


class ArtifactRepository:
    """成果物関連のデータアクセス層

    AI によって生成されたアーティファクト（成果物）のデータベース操作を提供します。
    アーティファクトの取得、トランザクション管理を担当します。
    """

    def __init__(self, session: AsyncSession):
        """ArtifactRepositoryを初期化する

        Args:
            session (AsyncSession): SQLAlchemyの非同期セッション
        """
        self.session = session

    @log_function_start_end
    async def get_artifact_by_id_and_version(
        self, artifact_id: uuid.UUID, version: int
    ) -> Optional[T_Artifact]:
        """成果物IDとバージョンで成果物を取得する

        指定されたアーティファクトIDとバージョン番号に基づいて
        データベースから該当する成果物を検索し取得します。

        Args:
            artifact_id (uuid.UUID): 成果物のID
            version (int): 成果物のバージョン番号

        Returns:
            Optional[T_Artifact]: 見つかった成果物オブジェクト、または None
        """
        select_stmt = select(T_Artifact).filter_by(
            artifact_id=artifact_id, version=version
        )
        result = await self.session.execute(select_stmt)
        return result.scalars().first()

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
