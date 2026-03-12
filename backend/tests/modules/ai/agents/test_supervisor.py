"""Supervisor agent のテスト

Agentクラスの主要な動作確認テスト。
実際のLLMとMeilisearchを使用した統合テストを含みます。
"""

import asyncio
import os
from datetime import datetime
from uuid import uuid4

import nanoid
import pytest
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from meilisearch_python_sdk import AsyncClient
from pytest_mock import MockerFixture

from qines_gai_backend.config.dependencies.data_connection import (
    User,
    get_connection_manager,
)
from qines_gai_backend.modules.ai.agents.supervisor import Agent
from qines_gai_backend.modules.collections.models import CollectionDetail
from qines_gai_backend.modules.conversations.models import Artifact, MessageMetadata
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
    "contents": "Specification for CAN XL Driver AUTOSAR CP R22-11 BusOff Handling",
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
        "test_qines-gai_supervisor", primary_key="id"
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
    await real_meili_client.index("test_qines-gai_supervisor").delete()


@pytest.fixture(scope="function")
async def initialize_connections():
    connection_manager = get_connection_manager()
    await connection_manager.connect_all()
    try:
        yield
    finally:
        await connection_manager.disconnect_all()


# //////////////////////////////////////////////////////////////////////
# TestAgentCreate - Agent作成のテスト
# //////////////////////////////////////////////////////////////////////


class TestAgentCreate:
    """Agent作成のテスト"""

    @pytest.mark.asyncio
    async def test_create_success(self, initialize_connections):
        """Agent作成成功のテスト"""
        collection = CollectionDetail(
            public_collection_id=nanoid.generate(size=11),
            name="test",
            documents=map_documents(TEST_DATA),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        agent = Agent(MOCK_USER.user_id, collection)
        assert agent is not None


# //////////////////////////////////////////////////////////////////////
# TestAgentAstream - Agent.astream のテスト（簡易的な統合テスト）
# //////////////////////////////////////////////////////////////////////


class TestAgentAstream:
    """Agent.astream の統合テスト

    注意: これらは実際のLLMとMeilisearchを使用する統合テストです。
    """

    @pytest.mark.asyncio
    async def test_astream_simple_message(
        self, initialize_connections, setup_real_index, mocker: MockerFixture
    ):
        """単純メッセージ処理のテスト"""
        index = setup_real_index.index("test_qines-gai_supervisor")
        mocker.patch("meilisearch_python_sdk.AsyncClient.index", return_value=index)

        collection = CollectionDetail(
            public_collection_id=nanoid.generate(size=11),
            name="test",
            documents=map_documents(TEST_DATA),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        agent = Agent(MOCK_USER.user_id, collection)

        buffer = ""
        async for msg in agent.astream(
            messages=[HumanMessage("CAN Driverについて簡単に教えて")],
            artifacts=[],
        ):
            if msg.type == "message":
                buffer += msg.content.content

        # 基本的な動作確認
        assert buffer != ""
        last_state = agent.get_state()
        last_message = last_state.messages[-1]
        assert buffer == last_message.content

    @pytest.mark.asyncio
    async def test_astream_with_artifact_creation(
        self, initialize_connections, setup_real_index, mocker: MockerFixture
    ):
        """Artifact生成を含む処理のテスト"""
        index = setup_real_index.index("test_qines-gai_supervisor")
        mocker.patch("meilisearch_python_sdk.AsyncClient.index", return_value=index)

        collection = CollectionDetail(
            public_collection_id=nanoid.generate(size=11),
            name="test",
            documents=map_documents(TEST_DATA),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        agent = Agent(MOCK_USER.user_id, collection)

        async for msg in agent.astream(
            messages=[
                HumanMessage("pythonでフィボナッチ数列のコードをArtifactに書いて")
            ],
            artifacts=[],
        ):
            pass  # メッセージを消費

        # Artifactが生成されたことを確認
        last_state = agent.get_state()
        assert len(last_state.artifacts) == 1
        assert len(last_state.artifact_operations) == 1

        last_message = last_state.messages[-1]
        metadata = last_message.additional_kwargs["qines_gai_metadata"]
        metadata = MessageMetadata.model_validate(metadata)
        assert len(metadata.generated_artifacts) == 1

    @pytest.mark.asyncio
    async def test_astream_with_artifact_editing(
        self, initialize_connections, setup_real_index, mocker: MockerFixture
    ):
        """Artifact編集を含む処理のテスト"""
        index = setup_real_index.index("test_qines-gai_supervisor")
        mocker.patch("meilisearch_python_sdk.AsyncClient.index", return_value=index)

        collection = CollectionDetail(
            public_collection_id=nanoid.generate(size=11),
            name="test",
            documents=map_documents(TEST_DATA),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        agent = Agent(MOCK_USER.user_id, collection)

        artifact_id = str(uuid4())
        artifact = Artifact(
            id=artifact_id,
            version=1,
            title="フィボナッチ数列の実装",
            content="""\
このアーティファクトでは、フィボナッチ数列のコードを提示します。

```py
def fibonacci_recursive(n):
    if n == 1:
        return 1
    elif n == 2:
        return 1
    else:
        return fibonacci_recursive(n-1) + fibonacci_recursive(n-2)
```
""",
        )

        async for msg in agent.astream(
            messages=[
                HumanMessage("フィボナッチ数列を書いて"),
                AIMessage(
                    f"以下にフィボナッチ数列のサンプルを示します。\ngenerated_artifact: 'artifact_id': {artifact_id}, 'version': 1"
                ),
                HumanMessage("さっきのコードをJavaScriptに変更してほしい"),
            ],
            artifacts=[artifact],
        ):
            pass  # メッセージを消費

        # Artifactが編集されたことを確認
        last_state = agent.get_state()
        assert len(last_state.artifacts) == 2  # 元のバージョン + 編集後のバージョン
        assert len(last_state.artifact_operations) == 1

        last_message = last_state.messages[-1]
        metadata = last_message.additional_kwargs["qines_gai_metadata"]
        metadata = MessageMetadata.model_validate(metadata)
        assert len(metadata.generated_artifacts) == 1
