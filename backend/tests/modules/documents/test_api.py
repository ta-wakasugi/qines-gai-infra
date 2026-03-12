"""Documents API統合テスト

httpx.AsyncClientを使用した統合テストにより、FastAPIのバリデーション(422)を含む
実際のHTTPリクエスト/レスポンスサイクルをテストする。

共通fixture（async_client, setup_user等）はconftest.pyで定義されています。
"""

import io
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from meilisearch_python_sdk.errors import MeilisearchApiError

from qines_gai_backend.config.dependencies.services import get_document_service
from qines_gai_backend.main import app
from qines_gai_backend.shared.exceptions import (
    BaseAppError,
    DocumentNotAuthorizedError,
    DocumentNotFoundError,
    DocumentValidationError,
)


@pytest.fixture
async def prepare_test_documents(test_data_creator):
    """テスト用のドキュメントデータを準備する"""
    doc_id = await test_data_creator.create_test_document(
        file_name="test_doc.pdf",
        file_path="/documents/test_doc.pdf",
        file_type="application/pdf",
        file_size=1024,
        user_id="test_user",
        metadata_info={"subject": "AUTOSAR", "genre": "SWS", "release": "R22-11"},
    )
    await test_data_creator.session.commit()
    return {"doc_id": doc_id}


class TestSearchDocumentAPI:
    """search_document (A002) の統合テスト"""

    @pytest.mark.asyncio
    async def test_search_document_success(self, async_client, prepare_test_documents):
        """正常系：ドキュメント検索が正常に実行できることを確認する"""
        response = await async_client.get(
            "/api/documents/search",
            params={
                "q": "test query",
                "hits_per_page": 5,
                "page": 1,
                "uploader[]": ["user"],
                "genre": "SWS",
                "release": "R22-11",
            },
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        result = response.json()
        assert "total_pages" in result
        assert "documents" in result
        assert isinstance(result["documents"], list)

    @pytest.mark.asyncio
    async def test_search_document_with_default_parameters(
        self, async_client, prepare_test_documents
    ):
        """正常系：デフォルトパラメータでの検索が成功することを確認する"""
        response = await async_client.get(
            "/api/documents/search",
            params={
                "hits_per_page": 7,
                "page": 1,
            },
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        result = response.json()
        assert "total_pages" in result
        assert "documents" in result

    @pytest.mark.asyncio
    async def test_search_document_with_empty_query(
        self, async_client, prepare_test_documents
    ):
        """正常系：空のクエリでの検索が成功することを確認する"""
        response = await async_client.get(
            "/api/documents/search",
            params={
                "q": "",
                "hits_per_page": 7,
                "page": 1,
            },
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        result = response.json()
        assert "total_pages" in result
        assert "documents" in result

    @pytest.mark.asyncio
    async def test_search_document_with_admin_uploader_only(
        self, async_client, prepare_test_documents
    ):
        """正常系：adminアップローダーのみでの検索が成功することを確認する"""
        response = await async_client.get(
            "/api/documents/search",
            params={
                "uploader[]": ["admin"],
            },
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        result = response.json()
        assert "total_pages" in result
        assert "documents" in result

    @pytest.mark.asyncio
    async def test_search_document_meilisearch_api_error(
        self, async_client, prepare_test_documents
    ):
        """異常系：MeilisearchAPIErrorで400が返ることを確認する"""
        # モックサービスを作成
        mock_service = AsyncMock()
        response_mock = MagicMock()
        response_mock.status_code = 400
        mock_service.search_documents.side_effect = MeilisearchApiError(
            "API Error", response=response_mock
        )

        # Dependency Injectionをオーバーライド
        app.dependency_overrides[get_document_service] = lambda: mock_service

        try:
            response = await async_client.get(
                "/api/documents/search",
                params={"q": "test query"},
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 400
            assert response.json()["detail"] == "Invalid query parameter value"
        finally:
            app.dependency_overrides.pop(get_document_service, None)

    @pytest.mark.asyncio
    async def test_search_document_base_app_error(
        self, async_client, prepare_test_documents
    ):
        """異常系：BaseAppErrorで500が返ることを確認する"""
        mock_service = AsyncMock()
        mock_service.search_documents.side_effect = BaseAppError("Service error")

        app.dependency_overrides[get_document_service] = lambda: mock_service

        try:
            response = await async_client.get(
                "/api/documents/search",
                params={"q": "test query"},
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal Server Error"
        finally:
            app.dependency_overrides.pop(get_document_service, None)


class TestUploadFileAPI:
    """upload_file (A016) の統合テスト"""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, async_client, prepare_test_documents):
        """正常系：ファイルアップロードが正常に完了することを確認する"""
        # モックサービスを使用（実際のPDF処理は複雑なため）
        from qines_gai_backend.modules.documents.models import DocumentBase

        mock_service = AsyncMock()
        mock_doc = DocumentBase(
            id=str(uuid.uuid4()),
            title="test.pdf",
            path="/test/path.pdf",
            subject="others",
            genre=None,
            release=None,
            file_type="application/pdf",
        )
        mock_service.upload_document.return_value = mock_doc

        app.dependency_overrides[get_document_service] = lambda: mock_service

        try:
            file_content = b"test content"
            files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}

            response = await async_client.post(
                "/api/documents/upload",
                files=files,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            result = response.json()
            assert "id" in result
            assert "title" in result
        finally:
            app.dependency_overrides.pop(get_document_service, None)

    @pytest.mark.asyncio
    async def test_upload_file_with_large_file(
        self, async_client, prepare_test_documents
    ):
        """正常系：大きなファイルでのアップロードが成功することを確認する"""
        # モックサービスを使用
        from qines_gai_backend.modules.documents.models import DocumentBase

        mock_service = AsyncMock()
        mock_doc = DocumentBase(
            id=str(uuid.uuid4()),
            title="large.pdf",
            path="/test/path.pdf",
            subject="others",
            genre=None,
            release=None,
            file_type="application/pdf",
        )
        mock_service.upload_document.return_value = mock_doc

        app.dependency_overrides[get_document_service] = lambda: mock_service

        try:
            # 5MBより小さいサイズのファイル（バリデーションを通過）
            file_content = b"x" * (4 * 1024 * 1024)  # 4MB
            files = {"file": ("large.pdf", io.BytesIO(file_content), "application/pdf")}

            response = await async_client.post(
                "/api/documents/upload",
                files=files,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            result = response.json()
            assert "id" in result
        finally:
            app.dependency_overrides.pop(get_document_service, None)

    @pytest.mark.asyncio
    async def test_upload_file_validation_error(
        self, async_client, prepare_test_documents
    ):
        """異常系：検証エラーで400が返ることを確認する"""
        mock_service = AsyncMock()
        mock_service.upload_document.side_effect = DocumentValidationError(
            "Invalid file format"
        )

        app.dependency_overrides[get_document_service] = lambda: mock_service

        try:
            file_content = b"test content"
            files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}

            response = await async_client.post(
                "/api/documents/upload",
                files=files,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 400
            assert "Invalid file format" in response.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_document_service, None)

    @pytest.mark.asyncio
    async def test_upload_file_base_app_error(
        self, async_client, prepare_test_documents
    ):
        """異常系：BaseAppErrorで500が返ることを確認する"""
        mock_service = AsyncMock()
        mock_service.upload_document.side_effect = BaseAppError("Upload failed")

        app.dependency_overrides[get_document_service] = lambda: mock_service

        try:
            file_content = b"test content"
            files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}

            response = await async_client.post(
                "/api/documents/upload",
                files=files,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500
            assert "Upload failed" in response.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_document_service, None)

    @pytest.mark.asyncio
    async def test_upload_file_general_exception(
        self, async_client, prepare_test_documents
    ):
        """異常系：一般的な例外で500が返ることを確認する"""
        mock_service = AsyncMock()
        mock_service.upload_document.side_effect = RuntimeError("Unexpected error")

        app.dependency_overrides[get_document_service] = lambda: mock_service

        try:
            file_content = b"test content"
            files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}

            response = await async_client.post(
                "/api/documents/upload",
                files=files,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal server error occurred"
        finally:
            app.dependency_overrides.pop(get_document_service, None)

    @pytest.mark.asyncio
    async def test_upload_file_missing_file(self, async_client, prepare_test_documents):
        """異常系：ファイルが指定されていない場合422が返ることを確認する"""
        # 空のfiles辞書を送る（ファイルなし）
        response = await async_client.post(
            "/api/documents/upload",
            files={},  # 空のmultipart/form-dataを送信
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 422


class TestDeleteDocumentAPI:
    """delete_document (A017) の統合テスト"""

    @pytest.mark.asyncio
    async def test_delete_document_success(self, async_client, prepare_test_documents):
        """正常系：ドキュメント削除が正常に完了することを確認する"""
        # モックサービスを使用（Meilisearchとの統合を避けるため）
        mock_service = AsyncMock()
        mock_service.delete_document.return_value = None

        app.dependency_overrides[get_document_service] = lambda: mock_service

        try:
            doc_id = prepare_test_documents["doc_id"]

            response = await async_client.delete(
                f"/api/documents/{doc_id}",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 204
        finally:
            app.dependency_overrides.pop(get_document_service, None)

    @pytest.mark.asyncio
    async def test_delete_document_with_uuid_format_id(
        self, async_client, prepare_test_documents
    ):
        """正常系：UUID形式のドキュメントIDでの削除が成功することを確認する"""
        # モックサービスを使用
        mock_service = AsyncMock()
        mock_service.delete_document.return_value = None

        app.dependency_overrides[get_document_service] = lambda: mock_service

        try:
            doc_id = prepare_test_documents["doc_id"]

            response = await async_client.delete(
                f"/api/documents/{doc_id}",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 204
        finally:
            app.dependency_overrides.pop(get_document_service, None)

    @pytest.mark.asyncio
    async def test_delete_document_with_special_characters_id(self, async_client):
        """正常系：特殊文字を含むドキュメントIDでの処理を確認する"""
        # モックサービスを使用（UUID形式でない場合はDocumentNotFoundErrorを発生）
        mock_service = AsyncMock()
        mock_service.delete_document.side_effect = DocumentNotFoundError(
            "Invalid document ID"
        )

        app.dependency_overrides[get_document_service] = lambda: mock_service

        try:
            # 特殊文字を含むIDは通常UUID形式でないため404になる
            doc_id = "doc_id-with-special.characters_123"

            response = await async_client.delete(
                f"/api/documents/{doc_id}",
                headers={"Authorization": "Bearer test_token"},
            )

            # UUID形式でないため404が返る
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_document_service, None)

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, async_client):
        """異常系：存在しないドキュメントIDの場合404が返ることを確認する"""
        # モックサービスを使用
        mock_service = AsyncMock()
        mock_service.delete_document.side_effect = DocumentNotFoundError(
            "Document not found"
        )

        app.dependency_overrides[get_document_service] = lambda: mock_service

        try:
            nonexistent_id = str(uuid.uuid4())

            response = await async_client.delete(
                f"/api/documents/{nonexistent_id}",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_document_service, None)

    @pytest.mark.asyncio
    async def test_delete_document_not_authorized(self, async_client):
        """異常系：権限がない場合403が返ることを確認する"""
        mock_service = AsyncMock()
        mock_service.delete_document.side_effect = DocumentNotAuthorizedError(
            "Not authorized"
        )

        app.dependency_overrides[get_document_service] = lambda: mock_service

        try:
            doc_id = str(uuid.uuid4())

            response = await async_client.delete(
                f"/api/documents/{doc_id}",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 403
            assert "Not authorized" in response.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_document_service, None)

    @pytest.mark.asyncio
    async def test_delete_document_base_app_error(self, async_client):
        """異常系：BaseAppErrorで500が返ることを確認する"""
        mock_service = AsyncMock()
        mock_service.delete_document.side_effect = BaseAppError("Deletion failed")

        app.dependency_overrides[get_document_service] = lambda: mock_service

        try:
            doc_id = str(uuid.uuid4())

            response = await async_client.delete(
                f"/api/documents/{doc_id}",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal Server Error"
        finally:
            app.dependency_overrides.pop(get_document_service, None)
