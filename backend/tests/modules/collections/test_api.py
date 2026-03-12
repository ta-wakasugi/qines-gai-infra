"""Collections API統合テスト

tests/apiの古いテストをsrcのディレクトリ構造に合わせて移行したもの。
AsyncClientを使用した統合テストにより、FastAPIのバリデーション(422)を含む
実際のHTTPリクエスト/レスポンスサイクルをテストする。

共通fixture（async_client, setup_user等）はconftest.pyで定義されています。
"""

import pytest

from qines_gai_backend.main import app


@pytest.fixture
async def prepare_test_documents(test_data_creator):
    """テスト用のドキュメントデータを準備する"""
    # conftestのTestDataCreatorを使って動的にドキュメントを作成（conftest.pyのcleanup_test_dataで自動削除される）
    doc1_id = await test_data_creator.create_test_document(
        file_name="test_doc1.pdf",
        file_path="/documents/test_doc1.pdf",
        file_type="application/pdf",
        file_size=1024,
        user_id="admin",
        metadata_info={"subject": "AUTOSAR", "genre": "SWS", "release": "R22-11"},
    )
    doc2_id = await test_data_creator.create_test_document(
        file_name="test_doc2.pdf",
        file_path="/documents/test_doc2.pdf",
        file_type="application/pdf",
        file_size=2048,
        user_id="admin",
        metadata_info={"subject": "AUTOSAR", "genre": "EXP", "release": "R23-11"},
    )
    await test_data_creator.session.commit()

    # 作成したドキュメントIDを返す（テストで使用）
    return {"doc1_id": doc1_id, "doc2_id": doc2_id}


class TestCreateCollectionAPI:
    """create_collection (A003) の統合テスト"""

    @pytest.mark.asyncio
    async def test_create_collection_success(
        self, async_client, prepare_test_documents
    ):
        """正常系：コレクションが正常に作成されることを確認する"""
        body = {
            "name": "Test Collection",
            "document_ids": [
                str(prepare_test_documents["doc1_id"]),
                str(prepare_test_documents["doc2_id"]),
            ],
        }

        response = await async_client.post(
            "/api/collections",
            json=body,
            headers={"Authorization": "Bearer test_token"},
        )

        result = response.json()
        assert response.status_code == 200
        assert result["name"] == body["name"]
        assert len(result["documents"]) == 2

    @pytest.mark.asyncio
    async def test_create_collection_invalid_uuid(
        self, async_client, prepare_test_documents
    ):
        """異常系：無効なUUID形式の場合422が返ることを確認する"""
        body = {
            "name": "Test Collection",
            "document_ids": ["invalid-uuid"],
        }

        response = await async_client.post(
            "/api/collections",
            json=body,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_collection_invalid_name_type(
        self, async_client, prepare_test_documents
    ):
        """異常系：nameの型が不正な場合422が返ることを確認する"""
        body = {
            "name": 123,  # 数値
            "document_ids": [str(prepare_test_documents["doc1_id"])],
        }

        response = await async_client.post(
            "/api/collections",
            json=body,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_collection_empty_documents(
        self, async_client, prepare_test_documents
    ):
        """正常系：document_idsが空でもコレクションが作成されることを確認する"""
        body = {
            "name": "Empty Collection",
            "document_ids": [],
        }

        response = await async_client.post(
            "/api/collections",
            json=body,
            headers={"Authorization": "Bearer test_token"},
        )

        result = response.json()
        assert response.status_code == 200
        assert result["name"] == body["name"]
        assert len(result["documents"]) == 0

    @pytest.mark.asyncio
    async def test_create_collection_base_app_error(
        self, async_client, prepare_test_documents
    ):
        """異常系：BaseAppErrorが発生した場合500が返ることを確認する"""
        from unittest.mock import AsyncMock
        from qines_gai_backend.shared.exceptions import BaseAppError
        from qines_gai_backend.config.dependencies.services import (
            get_collection_service,
        )

        # モックサービスを作成
        mock_service = AsyncMock()
        mock_service.create_collection.side_effect = BaseAppError("Database error")

        # Dependency Injectionをオーバーライド
        app.dependency_overrides[get_collection_service] = lambda: mock_service

        try:
            body = {
                "name": "Test Collection",
                "document_ids": [str(prepare_test_documents["doc1_id"])],
            }

            response = await async_client.post(
                "/api/collections",
                json=body,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal Server Error"
        finally:
            # テスト後にオーバーライドをクリア
            app.dependency_overrides.pop(get_collection_service, None)


class TestGetCollectionsAPI:
    """get_collections (A004) の統合テスト"""

    @pytest.mark.asyncio
    async def test_get_collections_success(self, async_client, prepare_test_documents):
        """正常系：コレクション一覧が正常に取得できることを確認する"""
        # まずコレクションを作成
        body = {
            "name": "Test Collection",
            "document_ids": [str(prepare_test_documents["doc1_id"])],
        }
        await async_client.post(
            "/api/collections",
            json=body,
            headers={"Authorization": "Bearer test_token"},
        )

        # 一覧を取得
        response = await async_client.get(
            "/api/collections",
            headers={"Authorization": "Bearer test_token"},
        )

        result = response.json()
        assert response.status_code == 200
        assert result["total"] >= 1
        assert len(result["collections"]) >= 1

    @pytest.mark.asyncio
    async def test_get_collections_with_negative_offset(
        self, async_client, prepare_test_documents
    ):
        """異常系：負のoffsetの場合422が返ることを確認する"""
        response = await async_client.get(
            "/api/collections?offset=-1",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_collections_base_app_error(
        self, async_client, prepare_test_documents
    ):
        """異常系：BaseAppErrorが発生した場合500が返ることを確認する"""
        from unittest.mock import AsyncMock
        from qines_gai_backend.shared.exceptions import BaseAppError
        from qines_gai_backend.config.dependencies.services import (
            get_collection_service,
        )

        mock_service = AsyncMock()
        mock_service.get_collections.side_effect = BaseAppError("Database error")
        app.dependency_overrides[get_collection_service] = lambda: mock_service

        try:
            response = await async_client.get(
                "/api/collections",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal Server Error"
        finally:
            app.dependency_overrides.pop(get_collection_service, None)


class TestUpdateCollectionAPI:
    """update_collection (A006) の統合テスト"""

    @pytest.mark.asyncio
    async def test_update_collection_success(
        self, async_client, prepare_test_documents
    ):
        """正常系：コレクションが正常に更新されることを確認する"""
        # まずコレクションを作成
        create_body = {
            "name": "Original Collection",
            "document_ids": [str(prepare_test_documents["doc1_id"])],
        }
        create_response = await async_client.post(
            "/api/collections",
            json=create_body,
            headers={"Authorization": "Bearer test_token"},
        )
        collection_id = create_response.json()["public_collection_id"]

        # 更新
        update_body = {
            "name": "Updated Collection",
            "document_ids": [
                str(prepare_test_documents["doc1_id"]),
                str(prepare_test_documents["doc2_id"]),
            ],
        }
        response = await async_client.put(
            f"/api/collections/{collection_id}",
            json=update_body,
            headers={"Authorization": "Bearer test_token"},
        )

        result = response.json()
        assert response.status_code == 200
        assert result["name"] == "Updated Collection"
        assert len(result["documents"]) == 2

    @pytest.mark.asyncio
    async def test_update_collection_invalid_uuid(
        self, async_client, prepare_test_documents
    ):
        """異常系：無効なUUID形式の場合422が返ることを確認する"""
        # まずコレクションを作成
        create_body = {
            "name": "Test Collection",
            "document_ids": [str(prepare_test_documents["doc1_id"])],
        }
        create_response = await async_client.post(
            "/api/collections",
            json=create_body,
            headers={"Authorization": "Bearer test_token"},
        )
        collection_id = create_response.json()["public_collection_id"]

        # 無効なUUIDで更新
        update_body = {
            "name": "Updated Collection",
            "document_ids": ["invalid-uuid"],
        }
        response = await async_client.put(
            f"/api/collections/{collection_id}",
            json=update_body,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_collection_not_found(
        self, async_client, prepare_test_documents
    ):
        """異常系：存在しないコレクションIDの場合404が返ることを確認する"""
        update_body = {
            "name": "Updated Collection",
            "document_ids": [str(prepare_test_documents["doc1_id"])],
        }
        response = await async_client.put(
            "/api/collections/nonexistent_id",
            json=update_body,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_collection_not_authorized(
        self, async_client, prepare_test_documents
    ):
        """異常系：権限がない場合403が返ることを確認する"""
        from unittest.mock import AsyncMock
        from qines_gai_backend.shared.exceptions import NotAuthorizedCollectionError
        from qines_gai_backend.config.dependencies.services import (
            get_collection_service,
        )

        mock_service = AsyncMock()
        mock_service.update_collection.side_effect = NotAuthorizedCollectionError()
        app.dependency_overrides[get_collection_service] = lambda: mock_service

        try:
            update_body = {
                "name": "Updated Collection",
                "document_ids": [str(prepare_test_documents["doc1_id"])],
            }
            response = await async_client.put(
                "/api/collections/some_id",
                json=update_body,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 403
        finally:
            app.dependency_overrides.pop(get_collection_service, None)

    @pytest.mark.asyncio
    async def test_update_collection_base_app_error(
        self, async_client, prepare_test_documents
    ):
        """異常系：BaseAppErrorが発生した場合500が返ることを確認する"""
        from unittest.mock import AsyncMock
        from qines_gai_backend.shared.exceptions import BaseAppError
        from qines_gai_backend.config.dependencies.services import (
            get_collection_service,
        )

        mock_service = AsyncMock()
        mock_service.update_collection.side_effect = BaseAppError("Database error")
        app.dependency_overrides[get_collection_service] = lambda: mock_service

        try:
            update_body = {
                "name": "Updated Collection",
                "document_ids": [str(prepare_test_documents["doc1_id"])],
            }
            response = await async_client.put(
                "/api/collections/some_id",
                json=update_body,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal Server Error"
        finally:
            app.dependency_overrides.pop(get_collection_service, None)


class TestGetCollectionDetailAPI:
    """get_collection (A005) の統合テスト"""

    @pytest.mark.asyncio
    async def test_get_collection_detail_success(
        self, async_client, prepare_test_documents
    ):
        """正常系：コレクション詳細が正常に取得できることを確認する"""
        # まずコレクションを作成
        create_body = {
            "name": "Test Collection",
            "document_ids": [str(prepare_test_documents["doc1_id"])],
        }
        create_response = await async_client.post(
            "/api/collections",
            json=create_body,
            headers={"Authorization": "Bearer test_token"},
        )
        collection_id = create_response.json()["public_collection_id"]

        # 詳細を取得
        response = await async_client.get(
            f"/api/collections/{collection_id}",
            headers={"Authorization": "Bearer test_token"},
        )

        result = response.json()
        assert response.status_code == 200
        assert result["name"] == "Test Collection"
        assert len(result["documents"]) == 1

    @pytest.mark.asyncio
    async def test_get_collection_detail_not_found(
        self, async_client, prepare_test_documents
    ):
        """異常系：存在しないコレクションIDの場合404が返ることを確認する"""
        response = await async_client.get(
            "/api/collections/nonexistent_id",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_collection_detail_not_authorized(
        self, async_client, prepare_test_documents
    ):
        """異常系：権限がない場合403が返ることを確認する"""
        from unittest.mock import AsyncMock
        from qines_gai_backend.shared.exceptions import NotAuthorizedCollectionError
        from qines_gai_backend.config.dependencies.services import (
            get_collection_service,
        )

        mock_service = AsyncMock()
        mock_service.get_collection_detail.side_effect = NotAuthorizedCollectionError()
        app.dependency_overrides[get_collection_service] = lambda: mock_service

        try:
            response = await async_client.get(
                "/api/collections/some_id",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 403
        finally:
            app.dependency_overrides.pop(get_collection_service, None)

    @pytest.mark.asyncio
    async def test_get_collection_detail_base_app_error(
        self, async_client, prepare_test_documents
    ):
        """異常系：BaseAppErrorが発生した場合500が返ることを確認する"""
        from unittest.mock import AsyncMock
        from qines_gai_backend.shared.exceptions import BaseAppError
        from qines_gai_backend.config.dependencies.services import (
            get_collection_service,
        )

        mock_service = AsyncMock()
        mock_service.get_collection_detail.side_effect = BaseAppError("Database error")
        app.dependency_overrides[get_collection_service] = lambda: mock_service

        try:
            response = await async_client.get(
                "/api/collections/some_id",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal Server Error"
        finally:
            app.dependency_overrides.pop(get_collection_service, None)


class TestGetConversationsAPI:
    """get_conversations (A008) の統合テスト"""

    @pytest.mark.asyncio
    async def test_get_conversations_success(
        self, async_client, prepare_test_documents
    ):
        """正常系：コレクションの会話一覧が取得できることを確認する"""
        # まずコレクションを作成
        create_body = {
            "name": "Test Collection",
            "document_ids": [str(prepare_test_documents["doc1_id"])],
        }
        create_response = await async_client.post(
            "/api/collections",
            json=create_body,
            headers={"Authorization": "Bearer test_token"},
        )
        collection_id = create_response.json()["public_collection_id"]

        # 会話一覧を取得
        response = await async_client.get(
            f"/api/collections/{collection_id}/conversations",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_conversations_not_found(
        self, async_client, prepare_test_documents, mocker
    ):
        """異常系：存在しないコレクションIDの場合404が返ることを確認する"""
        from qines_gai_backend.shared.exceptions import CollectionNotFoundError

        mock_service = mocker.patch(
            "qines_gai_backend.modules.collections.api.get_collection_service"
        )
        mock_service.return_value.get_collection_conversations.side_effect = (
            CollectionNotFoundError()
        )

        response = await async_client.get(
            "/api/collections/nonexistent_id/conversations",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_conversations_not_authorized(
        self, async_client, prepare_test_documents
    ):
        """異常系：権限がない場合403が返ることを確認する"""
        from unittest.mock import AsyncMock
        from qines_gai_backend.shared.exceptions import NotAuthorizedCollectionError
        from qines_gai_backend.config.dependencies.services import (
            get_collection_service,
        )

        mock_service = AsyncMock()
        mock_service.get_collection_conversations.side_effect = (
            NotAuthorizedCollectionError()
        )
        app.dependency_overrides[get_collection_service] = lambda: mock_service

        try:
            response = await async_client.get(
                "/api/collections/some_id/conversations",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 403
        finally:
            app.dependency_overrides.pop(get_collection_service, None)

    @pytest.mark.asyncio
    async def test_get_conversations_base_app_error(
        self, async_client, prepare_test_documents
    ):
        """異常系：BaseAppErrorが発生した場合500が返ることを確認する"""
        from unittest.mock import AsyncMock
        from qines_gai_backend.shared.exceptions import BaseAppError
        from qines_gai_backend.config.dependencies.services import (
            get_collection_service,
        )

        mock_service = AsyncMock()
        mock_service.get_collection_conversations.side_effect = BaseAppError(
            "Database error"
        )
        app.dependency_overrides[get_collection_service] = lambda: mock_service

        try:
            response = await async_client.get(
                "/api/collections/some_id/conversations",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal Server Error"
        finally:
            app.dependency_overrides.pop(get_collection_service, None)


class TestDeleteCollectionAPI:
    """delete_collection (A007) の統合テスト"""

    def test_delete_collection_unimplemented(self):
        """正常系：未実装のエンドポイントが呼べることを確認する"""
        from qines_gai_backend.modules.collections.api import delete_collection

        result = delete_collection("test_id")
        assert result is None


class TestShareCollectionAPI:
    """share_collection (A014) の統合テスト"""

    @pytest.mark.asyncio
    async def test_share_collection_unimplemented(self):
        """正常系：未実装のエンドポイントが呼べることを確認する"""
        from qines_gai_backend.modules.collections.api import share_collection

        result = await share_collection("test_id")
        assert result is None
