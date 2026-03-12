import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from botocore.exceptions import ClientError
from meilisearch_python_sdk import AsyncClient
from qines_gai_backend.config.dependencies.data_connection import (
    get_current_user,
    User,
    get_db_session,
    get_s3_client,
    get_connection_manager,
    get_meili_client,
)
from qines_gai_backend.config.external_resources.connections import ConnectionManager
from qines_gai_backend.config.external_resources.postgresql import PostgreSQLConnection
from qines_gai_backend.config.external_resources.meilisearch import (
    MeilisearchConnection,
)

# --- テストデータ ---
USER_INFO_FROM_VERIFY = {
    "sub": "keycloak-user-id",
    "email": "keycloak@example.com",
    "name": "KeycloakUser",
    "access_token": "valid_token",
}

################################
# Fixtures
################################


@pytest.fixture
def mock_connection_manager():
    """ConnectionManagerとリソース接続をモック"""
    mock_cm = MagicMock(spec=ConnectionManager)

    # Postgres async session context manager
    mock_pg_conn = MagicMock(spec=PostgreSQLConnection)

    class DummyAsyncSession:
        async def __aenter__(self):
            return "mock_db_session"

        async def __aexit__(self, exc_type, exc, tb):
            return False

    mock_pg_conn.get_session.return_value = DummyAsyncSession()

    # Meilisearch connection
    mock_meili_conn = MagicMock(spec=MeilisearchConnection)
    mock_meili_client = MagicMock(spec=AsyncClient)
    mock_meili_conn.get_client.return_value = mock_meili_client

    def get_connection_side_effect(kind: str):
        if kind == "postgresql":
            return mock_pg_conn
        if kind == "meilisearch":
            return mock_meili_conn
        return MagicMock()

    mock_cm.get_connection.side_effect = get_connection_side_effect
    return mock_cm


################################
# get_db_session
################################
@pytest.mark.asyncio
async def test_get_db_session(mock_connection_manager):
    gen = get_db_session(mock_connection_manager)
    session = await gen.__anext__()
    assert session == "mock_db_session"
    # ジェネレータを終了
    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()
    # DummyAsyncSession.__aexit__ は副作用不要なので呼び出し確認不要


################################
# get_meili_client
################################
@pytest.mark.asyncio
async def test_get_meili_client(mock_connection_manager):
    client = await get_meili_client(mock_connection_manager)
    # 2回呼ばれる可能性あるので回数より最後の引数確認
    assert any(
        call.args[0] == "meilisearch"
        for call in mock_connection_manager.get_connection.mock_calls
    )
    assert isinstance(client, MagicMock)


# --- get_s3_client 関数のテスト ---


def test_get_s3_client_production():
    """S3_ENDPOINT_URLが設定されていない場合、AWS S3に接続"""
    with patch.dict(os.environ, {}, clear=True):
        with patch("boto3.client") as mock_boto_client:
            client = get_s3_client()
            mock_boto_client.assert_called_once_with("s3")
            assert client is not None


def test_get_s3_client_with_endpoint():
    """S3_ENDPOINT_URLが設定されている場合、カスタムエンドポイントに接続"""
    test_env = {
        "S3_ENDPOINT_URL": "http://seaweedfs:8333",
        "AWS_ACCESS_KEY_ID": "testuser",
        "AWS_SECRET_ACCESS_KEY": "testpass",
    }
    with patch.dict(os.environ, test_env, clear=True):
        with patch("boto3.client") as mock_boto_client:
            client = get_s3_client()
            mock_boto_client.assert_called_once_with(
                "s3",
                endpoint_url="http://seaweedfs:8333",
                aws_access_key_id="testuser",
                aws_secret_access_key="testpass",
            )
            assert client is not None


def test_get_s3_client_with_endpoint_default_credentials():
    """S3_ENDPOINT_URLが設定されていて認証情報がない場合、デフォルト認証を使用"""
    test_env = {
        "S3_ENDPOINT_URL": "http://seaweedfs:8333",
    }
    with patch.dict(os.environ, test_env, clear=True):
        with patch("boto3.client") as mock_boto_client:
            client = get_s3_client()
            mock_boto_client.assert_called_once_with(
                "s3",
                endpoint_url="http://seaweedfs:8333",
                aws_access_key_id="admin",
                aws_secret_access_key="admin123",
            )
            assert client is not None


# --- get_connection_manager 関数のテスト ---


def test_get_connection_manager_cache():
    get_connection_manager.cache_clear()
    cm1 = get_connection_manager()
    cm2 = get_connection_manager()
    assert cm1 is cm2


# --- get_current_user 関数のテスト ---


def test_get_current_user_local_mode():
    test_env = {
        "APP_MODE": "local",
        "TEST_USER_ID": "local_user",
        "TEST_USER_EMAIL": "local@test.com",
    }
    with patch.dict(os.environ, test_env):
        user = get_current_user(auth=None)
        assert isinstance(user, User)
        assert user.user_id == "local_user"
        assert user.email == "local@test.com"


def test_get_current_user_no_auth_header():
    with patch.dict(os.environ, {"APP_MODE": "", "AUTH_PROVIDER": "cognito"}):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(auth=None)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authorization header missing"


def test_get_current_user_success():
    auth_creds = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="valid_token"
    )
    with patch.dict(
        os.environ,
        {
            "APP_MODE": "",
            "AUTH_PROVIDER": "cognito",
            "AWS_DEFAULT_REGION": "ap-northeast-1",
            "AWS_ACCESS_KEY_ID": "x",
            "AWS_SECRET_ACCESS_KEY": "y",
        },
    ):
        # boto3 client.get_user をモック
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.get_user.return_value = {
                "UserAttributes": [
                    {"Name": "sub", "Value": "cognito-sub"},
                    {"Name": "email", "Value": "user@example.com"},
                ]
            }
            mock_boto.return_value = mock_client
            user = get_current_user(auth=auth_creds)
            assert user.user_id == "cognito-sub"
            assert user.email == "user@example.com"
            mock_client.get_user.assert_called_once()


def test_get_current_user_client_error_not_authorized():
    auth_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad_token")
    with patch.dict(os.environ, {"APP_MODE": "", "AUTH_PROVIDER": "cognito"}):
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            error_response = {"Error": {"Code": "NotAuthorizedException"}}
            mock_client.get_user.side_effect = ClientError(error_response, "GetUser")
            mock_boto.return_value = mock_client
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(auth=auth_creds)
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid or expired token"


def test_get_current_user_client_error_other():
    auth_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad_token")
    with patch.dict(os.environ, {"APP_MODE": "", "AUTH_PROVIDER": "cognito"}):
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            error_response = {"Error": {"Code": "SomeOtherException"}}
            mock_client.get_user.side_effect = ClientError(error_response, "GetUser")
            mock_boto.return_value = mock_client
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(auth=auth_creds)
            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Error communication with AWS Cognito"


def test_get_current_user_unexpected_error():
    auth_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="any")
    with patch.dict(os.environ, {"APP_MODE": "", "AUTH_PROVIDER": "cognito"}):
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.get_user.side_effect = Exception("Boom")
            mock_boto.return_value = mock_client
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(auth=auth_creds)
            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Unexpected error occurred"
