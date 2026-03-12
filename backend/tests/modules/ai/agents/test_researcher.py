"""Researcher agent のテスト

Researcherクラスの主要な動作確認テスト。
実際のLLMとMeilisearchを使用した統合テストを含みます。
"""

import asyncio
import os
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from langchain_openai.chat_models import AzureChatOpenAI
from meilisearch_python_sdk import AsyncClient
from pytest_mock import MockerFixture

from qines_gai_backend.config.dependencies.data_connection import (
    User,
    get_connection_manager,
)
from qines_gai_backend.modules.ai.agents.researcher import Researcher
from qines_gai_backend.modules.ai.llm_wrapper import LLMWrapper
from qines_gai_backend.modules.collections.models import CollectionDetail
from qines_gai_backend.modules.documents.models import DocumentBase

load_dotenv("/app/.env")

MOCK_USER = User(user_id="test_user", email="test@example.com")

# テスト用データの定義
doc1 = {
    "id": "11111111-1111-1111-1111-111111111111",
    "doc_id": "00000000-0000-0000-00000000000000000",
    "title": "Specification for CAN XL Driver",
    "total_page": 10,
    "page_num": 1,
    "contents": "Specification for CAN XL Driver AUTOSAR CP R22-11",
    "subject": "AUTOSAR",
    "path": "/docs/autosar/specification1.pdf",
    "genre": "SWS",
    "release": "R23-11",
    "uploader": "admin",
    "file_type": "application/pdf",
}
doc2 = {
    "id": "22222222-2222-2222-2222-222222222222",
    "doc_id": "00000000-0000-0000-00000000000000000",
    "title": "Specification for CAN XL Driver",
    "total_page": 10,
    "page_num": 10,
    "contents": "Specification for CAN XL Driver AUTOSAR CP R22-11",
    "subject": "AUTOSAR",
    "path": "/docs/autosar/specification1.pdf",
    "genre": "SWS",
    "release": "R23-11",
    "uploader": "admin",
    "file_type": "application/pdf",
}
doc3 = {
    "id": "33333333-3333-3333-3333-333333333333",
    "doc_id": "11111111-1111-1111-11111111111111111",
    "title": "Specification for CAN Driver",
    "total_page": 40,
    "page_num": 10,
    "contents": "Specification of CAN Driver AUTOSAR CP R22-11",
    "subject": "AUTOSAR",
    "path": "/docs/autosar/specification1.pdf",
    "genre": "SWS",
    "release": "R23-11",
    "uploader": "admin",
    "file_type": "application/pdf",
}
TEST_DATA = [doc1, doc2, doc3]


def map_documents(docs):
    """検索結果をマッピングする用の関数"""
    return [
        DocumentBase.model_validate(
            {
                "id": doc["doc_id"],
                "title": doc["title"],
                "path": doc["path"],
                "subject": doc["subject"],
                "genre": doc["genre"] if doc["subject"] == "AUTOSAR" else None,
                "release": doc["release"] if doc["subject"] == "AUTOSAR" else None,
                "file_type": doc["file_type"],
            }
        )
        for doc in docs
    ]


@pytest.fixture(scope="function")
async def setup_real_index():
    """実際のmeilisearchクライアントに接続し、テスト用のインデックスを作成"""
    meilisearch_host = os.getenv("MEILISEARCH_HOST")
    real_meili_client = AsyncClient(meilisearch_host, None)
    real_index = await real_meili_client.create_index(
        "test_qines-gai_researcher", primary_key="id"
    )

    await real_index.update_filterable_attributes(
        ["genre", "release", "uploader", "doc_id", "chunk_num"]
    )
    task = await real_index.add_documents(TEST_DATA, primary_key="id")

    # タスク完了を待つ
    while True:
        status = await real_meili_client.get_task(task.task_uid)
        if status.status == "succeeded":
            break
        if status.status == "failed":
            raise Exception(f"task failed: {status.error}")
        await asyncio.sleep(0.1)

    yield real_meili_client
    await real_meili_client.index("test_qines-gai_researcher").delete()


@pytest.fixture(scope="function")
async def initialize_connections():
    connection_manager = get_connection_manager()
    await connection_manager.connect_all()
    try:
        yield
    finally:
        await connection_manager.disconnect_all()


# //////////////////////////////////////////////////////////////////////
# TestResearcherInit - Researcher初期化のテスト
# //////////////////////////////////////////////////////////////////////


class TestResearcherInit:
    """Researcher初期化のテスト"""

    def test_init_without_user_id(self, mocker: MockerFixture):
        """user_idが設定されていない場合、ValueErrorが送出される"""
        llm = mocker.Mock(spec=AzureChatOpenAI)
        collection = mocker.Mock(spec=CollectionDetail)

        with pytest.raises(ValueError):
            Researcher(llm, collection, {"configurable": {"thread_id": str(uuid4())}})

    def test_init_success(self, mocker: MockerFixture):
        """Researcher初期化成功"""
        llm = mocker.Mock(spec=AzureChatOpenAI)
        documents = map_documents(TEST_DATA)

        config = {
            "configurable": {"thread_id": str(uuid4()), "user_id": MOCK_USER.user_id}
        }

        researcher = Researcher(llm, documents, config)
        assert researcher is not None


# //////////////////////////////////////////////////////////////////////
# TestResearcherArun - Researcher.arun のテスト（簡易的な統合テスト）
# //////////////////////////////////////////////////////////////////////


class TestResearcherArun:
    """Researcher.arun の統合テスト

    注意: これらは実際のLLMとMeilisearchを使用する統合テストです。
    """

    @pytest.mark.asyncio
    async def test_arun_success(
        self, initialize_connections, setup_real_index, mocker: MockerFixture
    ):
        """調査実行成功のテスト"""
        index = setup_real_index.index("test_qines-gai_researcher")
        mocker.patch("meilisearch_python_sdk.AsyncClient.index", return_value=index)

        wrapper = LLMWrapper()
        llm = wrapper.get_llm(model_type=os.getenv("LLM_TYPE"), temperature=0)

        config = {
            "configurable": {"thread_id": str(uuid4()), "user_id": MOCK_USER.user_id}
        }

        researcher = Researcher(llm, map_documents(TEST_DATA), config)
        result = await researcher.arun("CAN Driverについて調査してください")

        # 基本的な動作確認
        assert result is not None
        assert len(result.messages) > 0

    @pytest.mark.asyncio
    async def test_arun_with_search(
        self, initialize_connections, setup_real_index, mocker: MockerFixture
    ):
        """検索を含む調査のテスト"""
        index = setup_real_index.index("test_qines-gai_researcher")
        mocker.patch("meilisearch_python_sdk.AsyncClient.index", return_value=index)

        wrapper = LLMWrapper()
        llm = wrapper.get_llm(model_type=os.getenv("LLM_TYPE"), temperature=0)

        config = {
            "configurable": {"thread_id": str(uuid4()), "user_id": MOCK_USER.user_id}
        }

        researcher = Researcher(llm, map_documents(TEST_DATA), config)
        result = await researcher.arun("AUTOSAR仕様について調査")

        # 基本的な動作確認
        assert result is not None
        assert len(result.messages) > 0
        # コンテキストが取得されたことを確認（検索が実行された証拠）
        assert len(result.contexts) > 0
