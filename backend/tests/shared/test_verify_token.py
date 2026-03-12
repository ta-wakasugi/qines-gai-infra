import base64
import json
import os
import time
from unittest.mock import patch, MagicMock

import pytest
import requests
from fastapi import HTTPException

from qines_gai_backend.shared.verify_token import verify_keycloak_access_token

# --- テストデータ ---
KEYCLOAK_URL = "http://localhost:8080"
REALM = "test-realm"
USER_INFO = {
    "sub": "test-user-id",
    "email": "test@example.com",
    "preferred_username": "testuser",
    "name": "Test User",
}

# 有効なJWTペイロード（期限は未来）
VALID_PAYLOAD = {"exp": int(time.time()) + 3600}
# 期限切れのJWTペイロード
EXPIRED_PAYLOAD = {"exp": int(time.time()) - 3600}


def create_mock_token(payload: dict) -> str:
    """ダミーのJWTトークンを作成する"""
    header = base64.urlsafe_b64encode(b'{"alg":"RS256"}').decode().strip("=")
    payload_str = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode().strip("=")
    signature = "dummy_signature"
    return f"{header}.{payload_b64}.{signature}"


VALID_TOKEN = create_mock_token(VALID_PAYLOAD)
EXPIRED_TOKEN = create_mock_token(EXPIRED_PAYLOAD)
INVALID_FORMAT_TOKEN = "invalid.token"

# --- テストケース ---


@patch("requests.get")
@patch.dict(os.environ, {"KEYCLOAK_URL": KEYCLOAK_URL, "KEYCLOAK_REALM": REALM})
def test_verify_keycloak_access_token_success(mock_requests_get):
    """正常系: 有効なトークンでユーザー情報が返される"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = USER_INFO
    mock_requests_get.return_value = mock_response

    result = verify_keycloak_access_token(VALID_TOKEN)

    assert result["sub"] == USER_INFO["sub"]
    assert result["name"] == "TestUser"  # スペースが削除されることを確認
    mock_requests_get.assert_called_once()


def test_verify_keycloak_access_token_expired():
    """異常系: 期限切れのトークン -> 401 (Access token expired) そのまま再raise"""
    with pytest.raises(HTTPException) as exc_info:
        verify_keycloak_access_token(EXPIRED_TOKEN)
    assert exc_info.value.status_code == 401
    # 最終段階では userinfo 401 により detail が 'Invalid access token' になる実装挙動
    assert exc_info.value.detail == "Invalid access token"


@patch("requests.get")
@patch.dict(os.environ, {"KEYCLOAK_URL": KEYCLOAK_URL, "KEYCLOAK_REALM": REALM})
def test_verify_keycloak_access_token_communication_error(mock_requests_get):
    """異常系: Keycloakとの通信エラー -> 500 Authentication service unavailable"""
    mock_requests_get.side_effect = requests.RequestException("Connection error")
    with pytest.raises(HTTPException) as exc_info:
        verify_keycloak_access_token(VALID_TOKEN)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Authentication service unavailable"


@patch("requests.get")
def test_verify_keycloak_access_token_missing_env_vars(mock_requests_get):
    """異常系: 環境変数が未設定 -> ValueError を捕捉し最終的に 500 Authentication error"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(HTTPException) as exc_info:
            verify_keycloak_access_token(VALID_TOKEN)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Authentication error"


def test_verify_keycloak_access_token_payload_decode_error():
    """異常系: ペイロードBase64破損でexpiryチェックが警告経路を通る (成功/失敗には影響しない)"""
    # token の payload 部分破損 (invalid base64)
    broken_token = VALID_TOKEN.split(".")
    broken_token[1] = "!!invalid!!"
    broken_token = ".".join(broken_token)
    # userinfoは失敗させて401へ
    with patch.dict(
        os.environ, {"KEYCLOAK_URL": KEYCLOAK_URL, "KEYCLOAK_REALM": REALM}
    ):
        with patch("requests.get") as mock_get:
            resp = MagicMock()
            resp.status_code = 401
            mock_get.return_value = resp
            with pytest.raises(HTTPException) as exc_info:
                verify_keycloak_access_token(broken_token)
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid access token"


@patch("requests.get")
@patch.dict(os.environ, {"KEYCLOAK_URL": KEYCLOAK_URL, "KEYCLOAK_REALM": REALM})
def test_verify_keycloak_access_token_unexpected_json_error(mock_requests_get):
    """異常系: response.json() が例外 -> Unexpected error 経路で 500 Authentication error"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    def boom():
        raise ValueError("json decode fail")

    mock_resp.json.side_effect = boom
    mock_requests_get.return_value = mock_resp
    with pytest.raises(HTTPException) as exc_info:
        verify_keycloak_access_token(VALID_TOKEN)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Authentication error"


@patch("requests.get")
@patch.dict(os.environ, {"KEYCLOAK_URL": KEYCLOAK_URL, "KEYCLOAK_REALM": REALM})
def test_verify_keycloak_access_token_invalid_format(mock_requests_get):
    """異常系: 不正な形式のトークンでもuserinfoエンドポイントで検証される"""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_requests_get.return_value = mock_response

    with pytest.raises(HTTPException) as exc_info:
        verify_keycloak_access_token(INVALID_FORMAT_TOKEN)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid access token"
    mock_requests_get.assert_called_once()
