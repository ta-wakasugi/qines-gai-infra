import os

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncEngine

from qines_gai_backend.config.external_resources.postgresql import PostgreSQLConnection


@pytest.fixture
async def postgres_connection():
    """
    PostgreSQLConnectionのインスタンスを提供し、テスト後にクリーンアップするフィクスチャ
    """
    connection = PostgreSQLConnection()
    yield connection
    await connection.disconnect()


async def test_connect(mocker: MockerFixture, postgres_connection):
    """
    `connect`メソッドの正常系テスト

    期待される動作:
        1. 環境変数から正しくURIを読み取る
        2. create_async_engineが正しい引数で呼び出される
        3. エンジンとセッションメーカーが正しく初期化される
    """
    mocker.patch.dict(os.environ, {"POSTGRES_URI": "postgresql+asyncpg://test"})

    await postgres_connection.connect()

    assert postgres_connection._engine is not None
    assert postgres_connection._AsyncSessionLocal is not None


async def test_connect_no_url(mocker: MockerFixture, postgres_connection):
    """
    `connect`メソッドの異常系テスト

    環境変数'POSTGRES_URI'が設定されていない場合:
        期待される動作:
            1. RuntimeErrorが発生する
    """
    mocker.patch.dict(os.environ, {}, clear=True)
    with pytest.raises(
        RuntimeError, match="PostgreSQLへの接続情報が設定されていません。"
    ):
        await postgres_connection.connect()


async def test_disconnect(mocker: MockerFixture, postgres_connection):
    """
    `disconnect`メソッドの正常系テスト

    期待される動作:
        1. エンジンの`dispose`メソッドが呼びだされる
        2. _engineがNoneに設定される
        3. _AsyncSessionLocalがNoneに設定される
    """
    mock_engine = mocker.AsyncMock(spec=AsyncEngine)
    postgres_connection._engine = mock_engine
    postgres_connection._AsyncSessionLocal = mocker.Mock()

    await postgres_connection.disconnect()

    mock_engine.dispose.assert_called_once()
    assert postgres_connection._engine is None
    assert postgres_connection._AsyncSessionLocal is None
