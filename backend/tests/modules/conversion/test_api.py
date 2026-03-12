"""ConversionモジュールのAPIエンドポイントのテスト

成果物からドキュメントへの変換処理を行うAPIエンドポイントの動作を検証します。
正常系のレスポンス、各種例外のHTTPステータスマッピング、リクエストバリデーションなどを含みます。
"""

import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import pytest

from qines_gai_backend.modules.conversion.api import router
from qines_gai_backend.config.dependencies.data_connection import User
from qines_gai_backend.shared.exceptions import (
    ArtifactNotFoundError,
    DocumentUpdateError,
    BaseAppError,
    DocumentUpdateValidationError,
)


class FakeService:
    """テスト用のConversionServiceダミー

    modeとpayloadを設定することで、任意の戻り値や例外を発生させることができます。
    """

    def __init__(self):
        # control attributes for behavior injection
        self.mode = "success"
        self.payload = {"document_id": str(uuid.uuid4()), "title": "OkTitle"}
        self.exc = None

    async def add_document_from_artifact(self, **_kwargs):
        """成果物から新規ドキュメントを作成するメソッドのダミー実装"""
        if self.mode == "raise":
            raise self.exc or DocumentUpdateError("no exception configured")
        return self.payload

    async def update_document_from_artifact(self, **_kwargs):
        """成果物から既存ドキュメントを更新するメソッドのダミー実装"""
        if self.mode == "raise":
            raise self.exc or DocumentUpdateError("no exception configured")
        return self.payload


@pytest.fixture
def app():
    """テスト用FastAPIアプリケーションを作成"""
    application = FastAPI()
    application.include_router(router)
    return application


@pytest.fixture
def client(app):
    """TestClientインスタンスを作成"""
    return TestClient(app)


@pytest.fixture
def fake_service():
    """FakeServiceインスタンスを作成"""
    return FakeService()


@pytest.fixture(autouse=True)
def override_dependencies(app, fake_service):
    """依存関係をモックで上書き

    テスト実行時に実際のサービスやデータベース接続を使用せず、
    ダミーサービスとモックで置き換えます。
    """
    from qines_gai_backend.config.dependencies.services import get_conversion_service
    from qines_gai_backend.config.dependencies.data_connection import (
        get_current_user,
        get_s3_client,
    )

    app.dependency_overrides[get_conversion_service] = lambda: fake_service
    app.dependency_overrides[get_current_user] = lambda: User(
        user_id="u1", email="u1@example.com"
    )
    app.dependency_overrides[get_s3_client] = lambda: MagicMock()
    yield
    app.dependency_overrides.clear()


# === Helper ===
VALID_BODY_ADD = {
    "public_collection_id": "12345678901",
    "artifact_id": str(uuid.uuid4()),
    "version": 1,
}
VALID_BODY_UPDATE = VALID_BODY_ADD.copy()

# === Success cases ===


def test_api_add_success(client, fake_service):
    """正常系：成果物から新規ドキュメント作成APIが成功することを確認

    - HTTPステータス200が返却される
    - レスポンスボディにsuccessフラグとdocument_idが含まれる
    """
    fake_service.mode = "success"
    r = client.post("/api/documents/from-artifact", json=VALID_BODY_ADD)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["document_id"] == fake_service.payload["document_id"]


def test_api_update_success(client, fake_service):
    """正常系：成果物からドキュメント更新APIが成功することを確認

    - HTTPステータス200が返却される
    - レスポンスボディにsuccessフラグが含まれる
    """
    fake_service.mode = "success"
    r = client.patch("/api/documents/from-artifact", json=VALID_BODY_UPDATE)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True


# === Error mapping cases (explicit exceptions) ===


def _run_raise(client, fake_service, method, exc, expected_status):
    """例外を発生させてHTTPステータスコードを検証するヘルパー関数"""
    fake_service.mode = "raise"
    fake_service.exc = exc
    if method == "add":
        resp = client.post("/api/documents/from-artifact", json=VALID_BODY_ADD)
    else:
        resp = client.patch("/api/documents/from-artifact", json=VALID_BODY_UPDATE)
    assert resp.status_code == expected_status, resp.text
    return resp


def test_api_add_artifact_not_found(client, fake_service):
    """異常系(ADD)：ArtifactNotFoundErrorが404にマッピングされることを確認"""
    _run_raise(client, fake_service, "add", ArtifactNotFoundError("nf"), 404)


def test_api_add_document_update_error(client, fake_service):
    """異常系(ADD)：DocumentUpdateErrorが500にマッピングされることを確認"""
    _run_raise(client, fake_service, "add", DocumentUpdateError("upd"), 500)


def test_api_add_base_app_error(client, fake_service):
    """異常系(ADD)：BaseAppErrorが500にマッピングされることを確認"""
    _run_raise(client, fake_service, "add", BaseAppError("base"), 500)


def test_api_add_validation_error(client, fake_service):
    """異常系(ADD)：DocumentUpdateValidationErrorが400にマッピングされることを確認"""
    _run_raise(client, fake_service, "add", DocumentUpdateValidationError("bad"), 400)


def test_api_add_unexpected_error(client, fake_service):
    """異常系(ADD)：予期しない例外が500にマッピングされることを確認"""
    _run_raise(client, fake_service, "add", Exception("boom"), 500)


def test_api_update_artifact_not_found(client, fake_service):
    """異常系(UPDATE)：ArtifactNotFoundErrorが404にマッピングされることを確認"""
    _run_raise(client, fake_service, "update", ArtifactNotFoundError("nf"), 404)


def test_api_update_document_update_error(client, fake_service):
    """異常系(UPDATE)：DocumentUpdateErrorが500にマッピングされることを確認"""
    _run_raise(client, fake_service, "update", DocumentUpdateError("upd"), 500)


def test_api_update_base_app_error(client, fake_service):
    """異常系(UPDATE)：BaseAppErrorが500にマッピングされることを確認"""
    _run_raise(client, fake_service, "update", BaseAppError("base"), 500)


def test_api_update_validation_error(client, fake_service):
    """異常系(UPDATE)：DocumentUpdateValidationErrorが400にマッピングされることを確認"""
    _run_raise(
        client, fake_service, "update", DocumentUpdateValidationError("bad"), 400
    )


def test_api_update_unexpected_error(client, fake_service):
    """異常系(UPDATE)：予期しない例外が500にマッピングされることを確認"""
    _run_raise(client, fake_service, "update", Exception("boom"), 500)


# === FastAPI request validation (UUID / nanoid length) ===


def test_api_add_validation_422(client):
    """異常系(ADD)：無効なUUID形式でリクエストした場合422が返却されることを確認

    FastAPI/Pydanticによるリクエストバリデーションエラーを検証します。
    """
    body = VALID_BODY_ADD.copy()
    body["artifact_id"] = (
        "not-a-uuid"  # triggers Pydantic validation -> 422 FastAPI layer
    )
    r = client.post("/api/documents/from-artifact", json=body)
    assert r.status_code == 422


def test_api_update_validation_422(client):
    """異常系(UPDATE)：不正な長さのpublic_collection_idで422が返却されることを確認

    FastAPI/Pydanticによるリクエストバリデーションエラーを検証します。
    """
    body = VALID_BODY_UPDATE.copy()
    body["public_collection_id"] = "short"  # length violation
    r = client.patch("/api/documents/from-artifact", json=body)
    assert r.status_code == 422
