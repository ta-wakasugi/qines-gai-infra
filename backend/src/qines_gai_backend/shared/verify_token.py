import base64
import json
import os
import time
from typing import Any, Dict

import requests
from fastapi import HTTPException

from qines_gai_backend.logger_config import get_logger

logger = get_logger(__name__)


def verify_keycloak_access_token(access_token: str) -> Dict[str, Any]:
    """Keycloakのアクセストークンを直接検証する。

    JWTアクセストークンの有効期限をチェックし、
    Keycloakのuserinfoエンドポイントを使用してトークンを検証する。

    Args:
        access_token (str): 検証対象のJWTアクセストークン

    Returns:
        Dict[str, Any]: ユーザー情報を含む辞書
            - sub: ユーザーID
            - email: メールアドレス
            - preferred_username: ユーザー名
            - name: 表示名
            - access_token: 元のアクセストークン

    Raises:
        HTTPException:
            - 401: トークンが無効または期限切れの場合
            - 500: Keycloakサービスとの通信エラーの場合
    """
    logger.info("Starting Keycloak access token verification")

    # 有効期限チェック
    token_parts = access_token.split(".")
    if len(token_parts) == 3:
        try:
            # ペイロードデコード
            payload_b64 = token_parts[1]
            payload_b64 += "=" * (4 - len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64).decode()
            payload_data = json.loads(payload_json)

            # 有効期限チェック
            if payload_data.get("exp"):
                current_time = int(time.time())
                exp_time = payload_data.get("exp")
                if current_time > exp_time:
                    logger.error("Access token has expired")
                    raise HTTPException(status_code=401, detail="Access token expired")

        except Exception as e:
            logger.warning(f"Failed to validate token expiry: {e}")

    try:
        keycloak_url = os.getenv("KEYCLOAK_URL")
        realm = os.getenv("KEYCLOAK_REALM")

        if not keycloak_url or not realm:
            logger.error(
                "Keycloak configuration missing (KEYCLOAK_URL or KEYCLOAK_REALM)"
            )
            raise ValueError("Keycloak configuration missing")

        # userinfoエンドポイントで検証
        userinfo_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/userinfo"
        logger.debug(
            f"Validating token with Keycloak userinfo endpoint: {userinfo_url}"
        )

        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(userinfo_url, headers=headers, timeout=10)

        if response.status_code == 200:
            logger.info("Keycloak access token validation successful")
            user_info = response.json()

            # 非機密情報のみログ出力
            logger.debug(f"Authenticated user_info: {user_info}")

            # 必要な情報を標準化して返す
            return {
                "sub": user_info.get("sub"),
                "email": user_info.get("email", "unknown@example.com"),
                "preferred_username": user_info.get("preferred_username"),
                "name": user_info.get("name", "").replace(" ", ""),
                "access_token": access_token,
            }
        else:
            logger.error(f"Keycloak validation failed (HTTP {response.status_code})")
            raise HTTPException(status_code=401, detail="Invalid access token")

    except requests.RequestException as e:
        logger.error(f"Keycloak service communication failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Authentication service unavailable"
        )
    except HTTPException:
        # HTTPExceptionは再raise
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication error")
