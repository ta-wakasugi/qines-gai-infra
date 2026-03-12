import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, AsyncGenerator

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from meilisearch_python_sdk import AsyncClient
from mypy_boto3_s3 import S3Client
from sqlalchemy.ext.asyncio import AsyncSession

from qines_gai_backend.config.external_resources.connections import ConnectionManager
from qines_gai_backend.config.external_resources.meilisearch import (
    MeilisearchConnection,
)
from qines_gai_backend.config.external_resources.postgresql import PostgreSQLConnection
from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.shared.verify_token import verify_keycloak_access_token

load_dotenv("/app/.env")
logger = get_logger(__name__)


@dataclass
class User:
    """ユーザー情報を表すデータクラス"""

    user_id: str
    email: str


@log_function_start_end
def get_current_user(
    auth: Annotated[
        HTTPAuthorizationCredentials,
        Depends(HTTPBearer(auto_error=False)),
    ],
):
    """リクエストしているユーザー情報を取得する関数

    この関数は、リクエストに付与されたAuthorizationヘッダに設定されたIDトークンを使用して、
    Cognito IdPもしくはKeycloakからユーザー情報を取得する。各APIエンドポイントで依存性注入されることを想定する。
    .envでローカルモードに設定されている場合は、.envのユーザ情報を取得し返却する。

    Args:
        auth (HTTPAuthorizationCredentials): Bearerトークンを含むHTTPAuthorizationCredentialsオブジェクト

    Returns:
        User: ユーザー情報を含むオブジェクト

    Raises:
        HTTPException:
            - 401: Authorizationヘッダが欠落もしくは対応していない認証スキームのとき
            - 401: 無効または期限切れのトークンのとき
            - 500: AWS CognitoもしくはKeycloakとの通信エラーが発生したとき
            - 500: Userオブジェクトの構築に失敗したとき
    """

    # ローカルモードの場合は、ローカルテスト用のユーザー情報取得し返却
    if os.getenv("APP_MODE") == "local":
        user_id = os.getenv("TEST_USER_ID")
        user_email = os.getenv("TEST_USER_EMAIL")
        logger.info("Local mode: using test user credentials")
        return User(user_id=user_id, email=user_email)

    provider = os.getenv("AUTH_PROVIDER")
    logger.info(f"provider:{provider}")

    if provider == "keycloak":
        logger.debug("Keycloak mode: processing token")

        if auth and auth.credentials:
            access_token = auth.credentials

            # JWTアクセストークンのみサポート
            if access_token.count(".") == 2 and access_token.startswith("eyJ"):
                logger.debug("Direct Keycloak JWT access token detected")
                try:
                    user_info = verify_keycloak_access_token(access_token)
                    logger.debug(
                        f"JWT validation successful for user: {user_info.get('email')}"
                    )
                    return User(user_id=user_info["sub"], email=user_info["email"])
                except Exception as e:
                    logger.error(f"JWT validation failed: {str(e)}")
                    raise HTTPException(
                        status_code=401, detail="Invalid Keycloak access token"
                    )
            else:
                # JWTトークン以外は認証エラー
                logger.error("Invalid token format - expected JWT access token")
                raise HTTPException(
                    status_code=401, detail="Direct Keycloak access token expected"
                )
        else:
            # Authorizationヘッダーがない場合は認証エラー
            logger.error("Authorization header missing in Keycloak mode")
            raise HTTPException(status_code=401, detail="Authorization header required")

    if not auth:
        # HTTPBearerを使うことで、"Bearer <token>"の形式でないものは全てNoneになる
        raise HTTPException(status_code=401, detail="Authorization header missing")

    # デフォルトはCognito認証
    try:
        access_token = auth.credentials
        client = boto3.client(
            "cognito-idp",
            region_name=os.getenv("AWS_DEFAULT_REGION"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        response = client.get_user(AccessToken=access_token)

        user_attributes = {
            attr["Name"]: attr["Value"] for attr in response["UserAttributes"]
        }

        user = User(
            user_id=user_attributes["sub"],
            email=user_attributes["email"],
        )

        return user
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NotAuthorizedException":
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        else:
            raise HTTPException(
                status_code=500, detail="Error communication with AWS Cognito"
            )
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


@lru_cache
@log_function_start_end
def get_connection_manager() -> ConnectionManager:
    """ConectionManagerのオブジェクトを返します。"""
    return ConnectionManager()


@log_function_start_end
async def get_db_session(
    connection_manager: ConnectionManager = Depends(get_connection_manager),
) -> AsyncGenerator[AsyncSession, None]:
    db: PostgreSQLConnection = connection_manager.get_connection("postgresql")
    async with db.get_session() as session:
        yield session


@log_function_start_end
async def get_meili_client(
    connection_manager: ConnectionManager = Depends(get_connection_manager),
) -> AsyncClient:
    meilisearch: MeilisearchConnection = connection_manager.get_connection(
        "meilisearch"
    )
    return meilisearch.get_client()


@log_function_start_end
def get_s3_client() -> S3Client:
    endpoint_url = os.getenv("S3_ENDPOINT_URL") or None
    if endpoint_url:
        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "admin"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "admin123"),
        )
    return boto3.client("s3")
