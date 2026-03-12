import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from qines_gai_backend.config.external_resources.base import ExternalResource


class PostgreSQLConnection(ExternalResource[AsyncEngine]):
    """PostgreSQLデータベースへの接続を管理するクラス。

    このクラスはPostgreSQLデータベースへの接続を管理し、
    SQLAlchemyを用いた非同期アクセスを提供します。

    接続設定は環境変数から読み込まれます：
        - POSTGRES_URI: PostgreSQLサーバーのURI

    Attributes:
        _engine: SQLAlchemyの非同期エンジンインスタンス。
        _sessionmaker: SQLAlchemyの非同期セッション生成インスタンス。
    """

    def __init__(self):
        """PostgreSQLConnectionを初期化します。"""
        self._engine: AsyncEngine | None = None
        self._AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        """PostgreSQLデータベースへの接続を確立します。

        環境変数から接続情報を読み込み、データベースへの接続を確立します。
        """
        if not self._engine:
            uri = os.getenv("POSTGRES_URI")

            if not uri:
                raise RuntimeError("PostgreSQLへの接続情報が設定されていません。")

            self._engine = create_async_engine(
                uri,
                echo=False,  # デバッグ用
            )
            if not self._AsyncSessionLocal:
                self._AsyncSessionLocal = async_sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self._engine,
                    class_=AsyncSession,
                )

    async def disconnect(self):
        """PostgreSQLデータベースとの接続を切断します。

        既存の接続をクローズし、接続プールを解放します。
        """
        if self._engine:
            await self._engine.dispose()  # 接続プールの解放
            self._engine = None
            self._AsyncSessionLocal = None

    def get_connection(self) -> AsyncEngine:
        """新しいPostgreSQLセッションを取得します。

        Returns:
            : SQLAlchemyの非同期エンジン。

        Raises:
            RuntimeError: 接続が初期化されていない場合。
        """
        if not self._engine:
            raise RuntimeError("PostgreSQLへの接続が初期化されていません。")
        return self._engine

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """新しいPostgreSQLセッションを取得します。

        Raises:
            RuntimeError: 接続が初期化されていない場合。
        """
        if not (self._engine and self._AsyncSessionLocal):
            raise RuntimeError("PostgreSQLへの接続が初期化されていません。")

        session = self._AsyncSessionLocal()
        try:
            yield session
        finally:
            await session.aclose()
