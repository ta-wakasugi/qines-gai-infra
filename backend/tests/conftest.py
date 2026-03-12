import uuid
from unittest.mock import MagicMock
from typing import Optional

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from qines_gai_backend.config.dependencies.data_connection import (
    User,
    get_connection_manager,
    get_current_user,
)
from qines_gai_backend.main import app
from qines_gai_backend.schemas.schema import (
    T_Artifact,
    T_Collection,
    T_CollectionDocument,
    T_Conversation,
    T_Document,
    T_Message,
)


# API統合テスト用の共通フィクスチャ
# Mock current user
mock_current_user = MagicMock(spec=User)


@pytest.fixture(scope="module")
def current_user():
    """モジュール全体で使用するユーザーオブジェクトのモックオブジェクトをセットアップする"""
    yield mock_current_user


@pytest.fixture(scope="function")
def setup_user(current_user):
    """ユーザーのモックオブジェクトの値をセットアップする"""
    user_mock = current_user.return_value
    user_mock.user_id = "test_user_id"
    user_mock.email = "test@example.com"
    yield user_mock


@pytest.fixture(scope="function")
async def async_client(setup_user):
    """非同期HTTPクライアントを作成する

    FastAPI統合テスト用のAsyncClientを提供する。
    認証をモックし、テスト後に自動的にdependency overridesをクリーンアップする。
    """
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://localhost:8000"
    ) as client:
        app.dependency_overrides[get_current_user] = lambda: setup_user
        yield client
        # テスト後のクリーンアップ
        app.dependency_overrides.clear()


# データベーステスト用の共通フィクスチャ
class TestDataCreator:
    """テストデータ作成用のユーティリティクラス"""

    def __init__(self, session):
        self.session = session

    async def create_test_collection(
        self, user_id: Optional[str] = None, **kwargs
    ) -> uuid.UUID:
        """テスト用のコレクションを作成し、collection_idを返す"""
        collection_id = uuid.uuid4()
        defaults = {
            "collection_id": collection_id,
            "public_collection_id": f"test_{uuid.uuid4().hex[:6]}",  # 11文字以内
            "user_id": user_id or "test_user_id",
            "name": "Test Collection",
        }
        defaults.update(kwargs)

        collection = T_Collection(**defaults)
        self.session.add(collection)
        await self.session.flush()
        return collection_id

    async def create_test_conversation(
        self, collection_id: uuid.UUID, user_id: Optional[str] = None, **kwargs
    ) -> uuid.UUID:
        """テスト用の会話履歴を作成し、conversation_idを返す"""
        conversation_id = uuid.uuid4()
        defaults = {
            "conversation_id": conversation_id,
            "public_conversation_id": f"test_{uuid.uuid4().hex[:6]}",  # 11文字以内
            "user_id": user_id or "test_user_id",
            "collection_id": collection_id,
            "title": "Test Conversation",
            "is_deleted": False,
        }
        defaults.update(kwargs)

        conversation = T_Conversation(**defaults)
        self.session.add(conversation)
        await self.session.flush()
        return conversation_id

    async def create_test_message(
        self, conversation_id: uuid.UUID, **kwargs
    ) -> uuid.UUID:
        """テスト用のメッセージを作成し、message_idを返す"""
        message_id = uuid.uuid4()
        defaults = {
            "message_id": message_id,
            "conversation_id": conversation_id,
            "sender_type": "user",
            "content": "Test message",
            "metadata_info": {"version": "v1"},
        }
        defaults.update(kwargs)

        message = T_Message(**defaults)
        self.session.add(message)
        await self.session.flush()
        return message_id

    async def create_test_artifact(
        self, conversation_id: uuid.UUID, message_id: uuid.UUID, **kwargs
    ) -> uuid.UUID:
        """テスト用の成果物を作成し、artifact_version_idを返す"""
        artifact_version_id = uuid.uuid4()
        artifact_id = uuid.uuid4()
        defaults = {
            "artifact_version_id": artifact_version_id,
            "message_id": message_id,
            "conversation_id": conversation_id,
            "artifact_id": artifact_id,
            "title": "Test Artifact",
            "version": 1,
            "content": "Test artifact content",
        }
        defaults.update(kwargs)

        artifact = T_Artifact(**defaults)
        self.session.add(artifact)
        await self.session.flush()
        return artifact_version_id

    async def create_test_document(
        self, user_id: Optional[str] = None, **kwargs
    ) -> uuid.UUID:
        """テスト用のドキュメントを作成し、document_idを返す"""
        document_id = uuid.uuid4()
        defaults = {
            "document_id": document_id,
            "file_name": "test_document.pdf",
            "file_path": "/test/path/test_document.pdf",
            "file_type": "application/pdf",
            "file_size": 1024,
            "user_id": user_id or "test_user_id",
            "is_shared": False,
            "metadata_info": {"subject": "AUTOSAR", "version": "v1"},
        }
        defaults.update(kwargs)

        document = T_Document(**defaults)
        self.session.add(document)
        await self.session.flush()
        return document_id

    async def create_test_collection_document(
        self, collection_id: uuid.UUID, document_id: uuid.UUID, **kwargs
    ) -> None:
        """テスト用のコレクションドキュメント関連を作成"""
        defaults = {
            "collection_id": collection_id,
            "document_id": document_id,
            "position": 1,
        }
        defaults.update(kwargs)

        collection_document = T_CollectionDocument(**defaults)
        self.session.add(collection_document)
        await self.session.flush()

    async def create_test_collection_with_documents(
        self, document_ids: list[uuid.UUID], **kwargs
    ) -> uuid.UUID:
        """テスト用のコレクションとドキュメント関連を一括作成"""
        collection_id = await self.create_test_collection(**kwargs)

        for index, document_id in enumerate(document_ids):
            await self.create_test_collection_document(
                collection_id=collection_id, document_id=document_id, position=index + 1
            )

        return collection_id

    async def create_test_conversation_with_messages_and_artifacts(
        self,
        collection_id: uuid.UUID,
        message_count: int = 2,
        artifact_count: int = 1,
        **kwargs,
    ) -> tuple[uuid.UUID, list[uuid.UUID], list[uuid.UUID]]:
        """テスト用の会話履歴、メッセージ、成果物を一括作成"""
        conversation_id = await self.create_test_conversation(collection_id, **kwargs)

        message_ids = []
        for i in range(message_count):
            sender_type = "user" if i % 2 == 0 else "ai"
            message_id = await self.create_test_message(
                conversation_id,
                sender_type=sender_type,
                content=f"Test message {i + 1}",
            )
            message_ids.append(message_id)

        artifact_ids = []
        if artifact_count > 0 and message_ids:
            for i in range(artifact_count):
                artifact_id = await self.create_test_artifact(
                    conversation_id,
                    message_ids[-1],  # 最後のメッセージに関連付け
                    title=f"Test Artifact {i + 1}",
                    version=i + 1,
                )
                artifact_ids.append(artifact_id)

        return conversation_id, message_ids, artifact_ids

    async def cleanup_test_data(self):
        """test_プレフィックスのテストデータを削除"""
        try:
            # 外部キー制約を考慮した順序で削除
            # まず削除対象のdocument_idを事前に取得
            target_document_ids_result = await self.session.execute(
                text(
                    "SELECT document_id FROM collection_documents WHERE collection_id IN (SELECT collection_id FROM collections WHERE public_collection_id LIKE 'test_%')"
                )
            )
            target_document_ids = [
                str(row[0]) for row in target_document_ids_result.fetchall()
            ]

            # artifacts テーブル
            await self.session.execute(
                text(
                    "DELETE FROM artifacts WHERE conversation_id IN (SELECT conversation_id FROM conversations WHERE public_conversation_id LIKE 'test_%')"
                )
            )

            # messages テーブル
            await self.session.execute(
                text(
                    "DELETE FROM messages WHERE conversation_id IN (SELECT conversation_id FROM conversations WHERE public_conversation_id LIKE 'test_%')"
                )
            )

            # conversations テーブル
            await self.session.execute(
                text(
                    "DELETE FROM conversations WHERE public_conversation_id LIKE 'test_%'"
                )
            )

            # collection_documents テーブル
            await self.session.execute(
                text(
                    "DELETE FROM collection_documents WHERE collection_id IN (SELECT collection_id FROM collections WHERE public_collection_id LIKE 'test_%')"
                )
            )

            # documents テーブル（事前に取得したdocument_idで削除）
            if target_document_ids:
                document_ids_str = "', '".join(target_document_ids)
                await self.session.execute(
                    text(
                        f"DELETE FROM documents WHERE document_id IN ('{document_ids_str}')"
                    )
                )

            # collections テーブル
            await self.session.execute(
                text("DELETE FROM collections WHERE public_collection_id LIKE 'test_%'")
            )

            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()

    async def get_test_data_counts(self) -> dict:
        """テストデータの件数を取得（デバッグ用）"""
        counts = {}
        tables = [
            (
                "collections",
                "SELECT COUNT(*) FROM collections WHERE public_collection_id LIKE 'test_%'",
            ),
            (
                "documents",
                "SELECT COUNT(*) FROM documents WHERE document_id IN (SELECT document_id FROM collection_documents WHERE collection_id IN (SELECT collection_id FROM collections WHERE public_collection_id LIKE 'test_%'))",
            ),
            (
                "collection_documents",
                "SELECT COUNT(*) FROM collection_documents WHERE collection_id IN (SELECT collection_id FROM collections WHERE public_collection_id LIKE 'test_%')",
            ),
            (
                "conversations",
                "SELECT COUNT(*) FROM conversations WHERE public_conversation_id LIKE 'test_%'",
            ),
            (
                "messages",
                "SELECT COUNT(*) FROM messages WHERE conversation_id IN (SELECT conversation_id FROM conversations WHERE public_conversation_id LIKE 'test_%')",
            ),
            (
                "artifacts",
                "SELECT COUNT(*) FROM artifacts WHERE conversation_id IN (SELECT conversation_id FROM conversations WHERE public_conversation_id LIKE 'test_%')",
            ),
        ]

        for table_name, query in tables:
            result = await self.session.execute(text(query))
            counts[table_name] = result.scalar() or 0

        return counts


# データベーステスト用の共通フィクスチャ
@pytest.fixture(scope="function")
async def initialize_connections():
    """DB接続の初期化を行う"""
    connection_manager = get_connection_manager()
    await connection_manager.connect_all()
    yield connection_manager
    # 各テスト後にテーブルのデータを削除
    async with connection_manager.get_connection("postgresql").get_session() as session:
        creator = TestDataCreator(session)
        await creator.cleanup_test_data()
    await connection_manager.disconnect_all()


@pytest.fixture
async def test_data_creator(initialize_connections):
    """TestDataCreatorのインスタンスを提供"""
    connection_manager = initialize_connections
    async with connection_manager.get_connection("postgresql").get_session() as session:
        yield TestDataCreator(session)


# テスト用サンプルデータのフィクスチャ
@pytest.fixture
def sample_conversation():
    """サンプルの会話履歴データを作成する"""
    conversation = MagicMock(spec=T_Conversation)
    conversation.conversation_id = uuid.uuid4()
    conversation.public_conversation_id = "test_conv_id"
    conversation.user_id = "test_user_id"
    conversation.title = "Test Conversation"
    return conversation


@pytest.fixture
def sample_messages():
    """サンプルのメッセージデータを作成する"""
    messages = []
    # userメッセージ
    user_message = MagicMock(spec=T_Message)
    user_message.sender_type = "user"
    user_message.content = "Test user message"
    user_message.metadata_info = {"version": "v1"}
    messages.append(user_message)

    # aiメッセージ
    ai_message = MagicMock(spec=T_Message)
    ai_message.sender_type = "ai"
    ai_message.content = "Test ai message"
    ai_message.metadata_info = {"version": "v1"}
    messages.append(ai_message)

    return messages


@pytest.fixture
def sample_artifacts():
    """サンプルの成果物データを作成する"""
    artifacts = []
    artifact = MagicMock(spec=T_Artifact)
    artifact.artifact_id = uuid.uuid4()
    artifact.version = 1
    artifact.title = "Test Artifact"
    artifact.content = "Test artifact content"
    artifacts.append(artifact)
    return artifacts


@pytest.fixture
def sample_collection():
    """サンプルのコレクションデータを作成する"""
    collection = MagicMock(spec=T_Collection)
    collection.collection_id = uuid.uuid4()
    collection.public_collection_id = "test_coll_id"
    collection.user_id = "test_user_id"
    collection.name = "Test Collection"
    collection.description = None
    return collection


@pytest.fixture
def sample_collection_document():
    """サンプルのコレクションドキュメント関連データを作成する"""
    collection_document = MagicMock(spec=T_CollectionDocument)
    collection_document.collection_id = uuid.uuid4()
    collection_document.document_id = uuid.uuid4()
    collection_document.position = 1
    return collection_document


# 各モジュール別のテスト用フィクスチャ
@pytest.fixture
async def collections_test_data(test_data_creator):
    """Collections モジュール用のテストデータセット"""
    # コレクションとドキュメントを作成
    document_id = await test_data_creator.create_test_document()
    collection_id = await test_data_creator.create_test_collection_with_documents(
        [document_id]
    )

    return {
        "collection_id": collection_id,
        "document_id": document_id,
    }


@pytest.fixture
async def conversations_test_data(test_data_creator):
    """Conversations モジュール用のテストデータセット"""
    # コレクション、会話履歴、メッセージ、成果物を作成
    collection_id = await test_data_creator.create_test_collection()
    (
        conversation_id,
        message_ids,
        artifact_ids,
    ) = await test_data_creator.create_test_conversation_with_messages_and_artifacts(
        collection_id
    )

    return {
        "collection_id": collection_id,
        "conversation_id": conversation_id,
        "message_ids": message_ids,
        "artifact_ids": artifact_ids,
    }


@pytest.fixture
async def documents_test_data(test_data_creator):
    """Documents モジュール用のテストデータセット"""
    # ドキュメントを作成
    document_id = await test_data_creator.create_test_document()

    return {
        "document_id": document_id,
    }


@pytest.fixture
async def artifacts_test_data(test_data_creator):
    """Artifacts モジュール用のテストデータセット"""
    # コレクション、会話履歴、メッセージ、成果物を作成
    collection_id = await test_data_creator.create_test_collection()
    conversation_id = await test_data_creator.create_test_conversation(collection_id)
    message_id = await test_data_creator.create_test_message(conversation_id)
    artifact_id = await test_data_creator.create_test_artifact(
        conversation_id, message_id
    )

    return {
        "collection_id": collection_id,
        "conversation_id": conversation_id,
        "message_id": message_id,
        "artifact_id": artifact_id,
    }


@pytest.fixture
async def ai_test_data(test_data_creator):
    """AI モジュール用のテストデータセット"""
    # ドキュメント、コレクション、会話履歴、メッセージ、成果物を一括作成
    document_id = await test_data_creator.create_test_document()
    collection_id = await test_data_creator.create_test_collection_with_documents(
        [document_id]
    )
    (
        conversation_id,
        message_ids,
        artifact_ids,
    ) = await test_data_creator.create_test_conversation_with_messages_and_artifacts(
        collection_id
    )

    return {
        "document_id": document_id,
        "collection_id": collection_id,
        "conversation_id": conversation_id,
        "message_ids": message_ids,
        "artifact_ids": artifact_ids,
    }


@pytest.fixture
async def conversion_test_data(test_data_creator):
    """Conversion モジュール用のテストデータセット"""
    # ドキュメントとコレクションを作成
    document_id = await test_data_creator.create_test_document()
    collection_id = await test_data_creator.create_test_collection_with_documents(
        [document_id]
    )

    return {
        "document_id": document_id,
        "collection_id": collection_id,
    }
