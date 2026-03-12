"""AI API統合テスト

AsyncClientを使用した統合テストにより、FastAPIのバリデーション(422)を含む
実際のHTTPリクエスト/レスポンスサイクルをテストする。

共通fixture（async_client, setup_user等）はconftest.pyで定義されています。
"""

import json
from unittest.mock import AsyncMock

import pytest

from qines_gai_backend.config.dependencies.services import get_ai_service
from qines_gai_backend.main import app
from qines_gai_backend.modules.collections.models import CollectionDetail
from qines_gai_backend.shared.exceptions import BaseAppError, CollectionCreationError


@pytest.fixture
async def prepare_test_collection(test_data_creator):
    """テスト用のコレクションデータを準備する"""
    # ドキュメントを作成
    doc1_id = await test_data_creator.create_test_document(
        file_name="test_doc1.pdf",
        file_path="/documents/test_doc1.pdf",
        file_type="application/pdf",
        file_size=1024,
        user_id="admin",
        metadata_info={"subject": "AUTOSAR", "genre": "SWS", "release": "R22-11"},
    )

    # コレクションを作成
    collection_id = await test_data_creator.create_test_collection(
        name="Test AI Collection",
        user_id="test_user",
    )

    # コレクションとドキュメントを関連付け
    from qines_gai_backend.schemas.schema import T_Collection, T_CollectionDocument

    collection = await test_data_creator.session.get(T_Collection, collection_id)

    # public_collection_idをcommit前に取得
    public_collection_id = collection.public_collection_id

    # CollectionDocumentを作成
    collection_document = T_CollectionDocument(
        collection_id=collection_id,
        document_id=doc1_id,
        position=0,
    )
    test_data_creator.session.add(collection_document)
    await test_data_creator.session.commit()

    return {
        "doc1_id": doc1_id,
        "collection_id": collection_id,
        "public_collection_id": public_collection_id,
    }


class TestCreateInitialCollectionAPI:
    """create_initial_collection (A012) の統合テスト"""

    @pytest.mark.asyncio
    async def test_create_initial_collection_success(self, async_client):
        """正常系：初期コレクションが正常に作成されることを確認する"""
        # モックサービスを作成
        mock_service = AsyncMock()
        mock_collection_detail = CollectionDetail(
            public_collection_id="test_col01",
            name="CAN仕様コレクション",
            documents=[],
            created_at="2023-01-01T00:00:00+09:00",
            updated_at="2023-01-01T00:00:00+09:00",
        )
        mock_service.create_initial_collection.return_value = mock_collection_detail

        # Dependency Injectionをオーバーライド
        app.dependency_overrides[get_ai_service] = lambda: mock_service

        try:
            body = {"message": "CAN仕様について教えて"}

            response = await async_client.post(
                "/api/ai/chat/start",
                json=body,
                headers={"Authorization": "Bearer test_token"},
            )

            result = response.json()
            assert response.status_code == 200
            assert result["public_collection_id"] == "test_col01"
            assert result["name"] == "CAN仕様コレクション"
            mock_service.create_initial_collection.assert_called_once()
        finally:
            app.dependency_overrides.pop(get_ai_service, None)

    @pytest.mark.asyncio
    async def test_create_initial_collection_service_error(self, async_client):
        """異常系：CollectionCreationErrorが発生した場合500が返ることを確認する"""
        mock_service = AsyncMock()
        mock_service.create_initial_collection.side_effect = CollectionCreationError(
            "Failed to create collection"
        )

        app.dependency_overrides[get_ai_service] = lambda: mock_service

        try:
            body = {"message": "test message"}

            response = await async_client.post(
                "/api/ai/chat/start",
                json=body,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500
            assert "Failed to create initial collection" in response.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_ai_service, None)

    @pytest.mark.asyncio
    async def test_create_initial_collection_base_app_error(self, async_client):
        """異常系：BaseAppErrorが発生した場合500が返ることを確認する"""
        mock_service = AsyncMock()
        mock_service.create_initial_collection.side_effect = BaseAppError(
            "Database error"
        )

        app.dependency_overrides[get_ai_service] = lambda: mock_service

        try:
            body = {"message": "test message"}

            response = await async_client.post(
                "/api/ai/chat/start",
                json=body,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal Server Error"
        finally:
            app.dependency_overrides.pop(get_ai_service, None)

    @pytest.mark.asyncio
    async def test_create_initial_collection_unexpected_error(self, async_client):
        """異常系：予期しないExceptionが発生した場合500が返ることを確認する"""
        mock_service = AsyncMock()
        mock_service.create_initial_collection.side_effect = Exception(
            "Unexpected error"
        )

        app.dependency_overrides[get_ai_service] = lambda: mock_service

        try:
            body = {"message": "test message"}

            response = await async_client.post(
                "/api/ai/chat/start",
                json=body,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal Server Error"
        finally:
            app.dependency_overrides.pop(get_ai_service, None)


class TestStreamChatAPI:
    """stream_chat (A013) の統合テスト"""

    @pytest.mark.asyncio
    async def test_stream_chat_new_conversation(
        self, async_client, prepare_test_collection
    ):
        """正常系：新規会話でのストリーミングが成功することを確認する"""
        # モックサービスを作成
        mock_service = AsyncMock()
        mock_service.validate_stream_chat_request = AsyncMock(return_value=None)

        async def mock_stream_chat(user_id, request):
            yield '{"public_conversation_id": "conv01", "message": {"role": "assistant", "content": "Hello"}}\n'
            yield '{"public_conversation_id": "conv01", "message": {"role": "assistant", "content": " World"}}\n'

        mock_service.stream_chat = mock_stream_chat

        app.dependency_overrides[get_ai_service] = lambda: mock_service

        try:
            body = {
                "message": "test message",
                "public_collection_id": prepare_test_collection["public_collection_id"],
            }

            response = await async_client.post(
                "/api/ai/chat/completions",
                json=body,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/x-ndjson"

            # ストリーミングレスポンスの確認
            content = response.text
            lines = content.strip().split("\n")
            assert len(lines) == 2

            # 各行がJSONパース可能であることを確認
            for line in lines:
                data = json.loads(line)
                assert "public_conversation_id" in data
                assert data["public_conversation_id"] == "conv01"
        finally:
            app.dependency_overrides.pop(get_ai_service, None)

    @pytest.mark.asyncio
    async def test_stream_chat_existing_conversation(
        self, async_client, prepare_test_collection
    ):
        """正常系：既存会話での継続ストリーミングが成功することを確認する"""
        mock_service = AsyncMock()
        mock_service.validate_stream_chat_request = AsyncMock(return_value=None)

        async def mock_stream_chat(user_id, request):
            yield '{"public_conversation_id": "conv01", "message": {"role": "assistant", "content": "Response"}}\n'

        mock_service.stream_chat = mock_stream_chat

        app.dependency_overrides[get_ai_service] = lambda: mock_service

        try:
            body = {
                "message": "test message",
                "public_collection_id": prepare_test_collection["public_collection_id"],
                "public_conversation_id": "conv01",
            }

            response = await async_client.post(
                "/api/ai/chat/completions",
                json=body,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            content = response.text
            lines = content.strip().split("\n")
            assert len(lines) == 1
        finally:
            app.dependency_overrides.pop(get_ai_service, None)

    @pytest.mark.asyncio
    async def test_stream_chat_collection_not_found(
        self, async_client, prepare_test_collection
    ):
        """異常系：コレクションが見つからない場合404が返ることを確認する"""
        from fastapi import HTTPException

        mock_service = AsyncMock()
        mock_service.validate_stream_chat_request.side_effect = HTTPException(
            status_code=404, detail="Collection not found"
        )

        app.dependency_overrides[get_ai_service] = lambda: mock_service

        try:
            body = {
                "message": "test message",
                "public_collection_id": "nonexistent",
            }

            response = await async_client.post(
                "/api/ai/chat/completions",
                json=body,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 404
            assert "Collection not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_ai_service, None)

    @pytest.mark.asyncio
    async def test_stream_chat_not_authorized(
        self, async_client, prepare_test_collection
    ):
        """異常系：権限がない場合403が返ることを確認する"""
        from fastapi import HTTPException

        mock_service = AsyncMock()
        mock_service.validate_stream_chat_request.side_effect = HTTPException(
            status_code=403, detail="Not authorized to use this collection"
        )

        app.dependency_overrides[get_ai_service] = lambda: mock_service

        try:
            body = {
                "message": "test message",
                "public_collection_id": prepare_test_collection["public_collection_id"],
            }

            response = await async_client.post(
                "/api/ai/chat/completions",
                json=body,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 403
            assert "Not authorized to use this collection" in response.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_ai_service, None)


class TestTranslateTextAPI:
    """translate_text (A011) の統合テスト"""

    @pytest.mark.asyncio
    async def test_translate_text_deprecated(self, async_client):
        """正常系：非推奨エンドポイントの動作確認"""
        body = {"text": "Test message"}

        response = await async_client.post(
            "/api/ai/translate",
            json=body,
        )

        # エンドポイントは非推奨で未実装（空のTranslatedTextを返す）
        assert response.status_code == 200
        assert response.json() == {"result": ""}
