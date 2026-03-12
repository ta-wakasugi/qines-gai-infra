import os

import boto3
import pytest
from botocore.exceptions import ClientError
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from moto import mock_aws
from pytest_mock import MockerFixture

from qines_gai_backend.config.dependencies.data_connection import User, get_current_user

app = FastAPI()


@app.get("/test-auth")
async def mock_auth(user: User = Depends(get_current_user)):
    return {"user_id": user.user_id, "email": user.email}


client = TestClient(app)


@pytest.fixture(scope="function")
def aws_credentials():
    """AWSの認証情報をモックするためのフィクスチャ"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-northeast-1"
    os.environ["APP_MODE"] = ""
    os.environ["AUTH_PROVIDER"] = "cognito"


@pytest.fixture(scope="function")
def cognito_client(aws_credentials):
    """Cognitoクライアントをモックするためのフィクスチャ"""
    with mock_aws():
        yield boto3.client(
            "cognito-idp",
            region_name=os.getenv("AWS_DEFAULT_REGION"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )


def test_get_current_user_success(cognito_client):
    """`get_current_user`関数の正常系テスト

    有効なアクセストークンでユーザー情報を取得できることを確認する
    期待される動作:
        1. ステータスコードが200である
        2. レスポンスボディにuser_id, name, emailが含まれている
        3. レスポンスボディの各値がCognitoに登録された値と一致している
    """
    # Cognitoユーザープールとユーザーの作成
    user_pool_id = cognito_client.create_user_pool(
        PoolName="test-pool",
        UsernameAttributes=["email"],
        AutoVerifiedAttributes=["email"],
    )["UserPool"]["Id"]

    # ユーザーの登録
    cognito_client.admin_create_user(
        UserPoolId=user_pool_id,
        Username="testuser@example.com",
        UserAttributes=[{"Name": "email", "Value": "testuser@example.com"}],
        TemporaryPassword="TemporaryPassword123!",
    )

    # ユーザーの確認
    cognito_client.admin_set_user_password(
        UserPoolId=user_pool_id,
        Username="testuser@example.com",
        Password="NewStrongPassword!123",
        Permanent=True,
    )

    # ユーザーの認証とアクセストークンの取得
    client_id = cognito_client.create_user_pool_client(
        UserPoolId=user_pool_id, ClientName="test-client"
    )["UserPoolClient"]["ClientId"]

    auth_response = cognito_client.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": "testuser@example.com",
            "PASSWORD": "NewStrongPassword!123",
        },
    )
    access_token = auth_response["AuthenticationResult"]["AccessToken"]

    response = client.get(
        "/test-auth", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    user_data = response.json()
    assert "user_id" in user_data
    assert user_data["email"] == "testuser@example.com"


def test_get_current_user_missing_or_invalid_auth_header():
    """`get_current_user`の異常系テスト

    Authorizationヘッダーが欠落している場合:
        期待される動作:
            1. ステータスコードが401である
            2. エラーメッセージが"Authorization header missing"である
    """
    response = client.get("/test-auth")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authorization header missing"


def test_get_current_user_invalid_token():
    """`get_current_user`の異常系テスト

    無効なアクセストークンでリクエストした場合:
        期待される動作:
            1. ステータスコードが401である
            2. エラーメッセージが"Invalid or expired token"である
    """
    response = client.get(
        "/test-auth", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_get_current_user_aws_communication_error(mocker: MockerFixture):
    """`get_current_user`の異常系テスト

    AWSと通信する処理において、認証以外のエラーが発生した場合:
        期待される動作:
            1. ステータスコードが500である
            2. エラーメッセージが"Error Communication with AWS Cognito"である
    """
    mock_client = mocker.patch("boto3.client")
    mock_get_user = mocker.Mock()
    mock_get_user.side_effect = ClientError(
        operation_name="test",
        error_response={
            "Error": {"Code": "ServiceError", "Message": "Mocked Error Message"}
        },
    )
    mock_client.return_value.get_user = mock_get_user

    response = client.get("/test-auth", headers={"Authorization": "Bearer valid_token"})
    assert response.status_code == 500
    assert response.json()["detail"] == "Error communication with AWS Cognito"


def test_get_current_user_missing_user_attributes(mocker: MockerFixture):
    """`get_current_user`の異常系テスト

    Cognitoの応答にユーザー属性が欠落している場合:
        期待される動作:
            1. ステータスコードが500である
            2. エラーメッセージが"Unexpected error occured"
    """
    mock_client = mocker.patch("boto3.client")
    mock_get_user = mocker.Mock()
    mock_get_user.return_value = {
        "Username": "testuser",
        "UserAttributes": [
            {"Name": "NAME", "Value": "testuser"},
            {"Name": "EMAIL", "Value": "testuser@example.com"},
        ],
    }
    mock_client.return_value.get_user = mock_get_user

    response = client.get("/test-auth", headers={"Authorization": "Bearer valid_token"})

    assert response.status_code == 500
    assert response.json()["detail"] == "Unexpected error occurred"
