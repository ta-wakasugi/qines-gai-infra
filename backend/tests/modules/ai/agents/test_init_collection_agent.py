"""InitCollectionAgent のテスト

InitCollectionAgentクラスの主要な動作確認テスト。
モックを使用した単体テストを含みます。
"""

import json
from unittest.mock import AsyncMock

import pytest

from qines_gai_backend.config.dependencies.data_connection import get_connection_manager
from qines_gai_backend.modules.ai.agents.init_collection_agent import (
    InitCollectionAgent,
)


@pytest.fixture(scope="function")
async def initialize_connections():
    connection_manager = get_connection_manager()
    await connection_manager.connect_all()
    try:
        yield
    finally:
        await connection_manager.disconnect_all()


# //////////////////////////////////////////////////////////////////////
# TestInitCollectionAgent - InitCollectionAgent.collection のテスト
# //////////////////////////////////////////////////////////////////////


class TestInitCollectionAgent:
    """InitCollectionAgent.collection のテスト"""

    @pytest.mark.asyncio
    async def test_collection_success(self, mocker, initialize_connections):
        """コレクション生成成功のテスト（2件ヒット）"""
        mock_hits = [
            {
                "id": 1,
                "content": "Example content...",
                "doc_id": "11111111-1111-1111-1111-111111111111",
            },
            {
                "id": 2,
                "content": "Another example...",
                "doc_id": "22222222-2222-2222-2222-222222222222",
            },
        ]

        mock_meili_client = mocker.Mock()
        mock_index = mocker.Mock()
        mock_index.search = AsyncMock(return_value=mocker.AsyncMock(hits=mock_hits))
        mock_meili_client.index.return_value = mock_index

        agent = InitCollectionAgent()
        query = "ブレーキに関する資料を探してください。"
        result_json = await agent.collection(mock_meili_client, query)

        result_dic = json.loads(result_json)
        assert set(result_dic["document_ids"]) == set(
            [
                "11111111-1111-1111-1111-111111111111",
                "22222222-2222-2222-2222-222222222222",
            ]
        )
        assert result_dic["name"] is not None

    @pytest.mark.asyncio
    async def test_collection_with_empty_result(self, mocker, initialize_connections):
        """コレクション生成成功のテスト（0件ヒット）"""
        mock_hits = []

        mock_meili_client = mocker.Mock()
        mock_index = mocker.Mock()
        mock_index.search = AsyncMock(return_value=mocker.AsyncMock(hits=mock_hits))
        mock_meili_client.index.return_value = mock_index

        agent = InitCollectionAgent()
        query = "存在しない資料を探してください。"
        result_json = await agent.collection(mock_meili_client, query)

        result_dic = json.loads(result_json)
        assert set(result_dic["document_ids"]) == set([])
        assert result_dic["name"] is not None

    @pytest.mark.asyncio
    async def test_collection_with_multiple_docs(self, mocker, initialize_connections):
        """コレクション生成成功のテスト（5件以上ヒット）"""
        mock_hits = [
            {
                "id": i,
                "content": f"Content {i}",
                "doc_id": f"00000000-0000-0000-0000-00000000000{i}",
            }
            for i in range(1, 8)
        ]

        mock_meili_client = mocker.Mock()
        mock_index = mocker.Mock()
        mock_index.search = AsyncMock(return_value=mocker.AsyncMock(hits=mock_hits))
        mock_meili_client.index.return_value = mock_index

        agent = InitCollectionAgent()
        query = "エンジンに関する資料を探してください。"
        result_json = await agent.collection(mock_meili_client, query)

        result_dic = json.loads(result_json)
        # ドキュメントIDが取得されていることを確認
        assert len(result_dic["document_ids"]) > 0
        assert result_dic["name"] is not None
