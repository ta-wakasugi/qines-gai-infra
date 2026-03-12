"""Conversionモジュールのリポジトリクラスのテスト

成果物からドキュメントへの変換処理におけるデータベース操作を検証します。
トランザクション管理、エラーハンドリング、コレクションへのドキュメント追加などを含みます。
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from qines_gai_backend.modules.conversion.repositories import ConversionRepository
from qines_gai_backend.shared.exceptions import (
    CollectionNotFoundError,
    DocumentUpdateError,
)


# シンプルなダミーエンティティ
class _DummyCollection:
    """テスト用のダミーコレクションエンティティ"""

    def __init__(self, collection_id):
        self.collection_id = collection_id


class _DummyCollectionDocument:
    """テスト用のダミーコレクションドキュメントエンティティ"""

    def __init__(self, collection_id, document_id, position):
        self.collection_id = collection_id
        self.document_id = document_id
        self.position = position


@pytest.fixture()
def conv_session():
    """ConversionRepositoryテスト用のモックセッションを作成"""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture()
def conv_meili():
    """ConversionRepositoryテスト用のモックMeilisearchクライアントを作成"""
    return AsyncMock()


@pytest.fixture()
def conv_repo(conv_session, conv_meili):
    """ConversionRepositoryのインスタンスを作成"""
    return ConversionRepository(conv_session, conv_meili)


def _result_builder(value=None, scalar_value=None):
    """SQLAlchemyのクエリ結果をモック化するヘルパー関数"""

    class _S:
        def __init__(self, v):
            self._v = v

        def first(self):
            return self._v

    class _R:
        def __init__(self, v, sv):
            self._v = v
            self._sv = sv

        def scalars(self):
            return _S(self._v)

        def scalar(self):
            return self._sv

    return _R(value, scalar_value)


@pytest.mark.asyncio
async def test_add_document_new_success(conv_repo, conv_session):
    """新規ドキュメントを正常に追加できることを確認"""
    dummy_collection = _DummyCollection(uuid.uuid4())
    state = {"step": 0}

    async def side_effect(_stmt):  # _stmt unused
        state["step"] += 1
        if state["step"] == 1:  # collection fetch
            return _result_builder(value=dummy_collection)
        if state["step"] == 2:  # existing fetch (None)
            return _result_builder(value=None)
        return _result_builder(scalar_value=0)  # count

    conv_session.execute.side_effect = side_effect
    await conv_repo.add_document_to_collection("pub_id", str(uuid.uuid4()))
    conv_session.add.assert_called_once()
    assert conv_session.flush.await_count == 1


@pytest.mark.asyncio
async def test_add_document_skip_existing(conv_repo, conv_session):
    """既に存在するドキュメントは追加をスキップすることを確認"""
    dummy_collection = _DummyCollection(uuid.uuid4())
    dummy_existing = _DummyCollectionDocument(
        dummy_collection.collection_id, uuid.uuid4(), 1
    )
    state = {"step": 0}

    async def side_effect(stmt):
        state["step"] += 1
        if state["step"] == 1:
            return _result_builder(value=dummy_collection)
        if state["step"] == 2:  # existing found
            return _result_builder(value=dummy_existing)
        return _result_builder(scalar_value=1)

    conv_session.execute.side_effect = side_effect
    await conv_repo.add_document_to_collection("pub_id", str(uuid.uuid4()))
    conv_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_add_document_add_flag_forces_insert(conv_repo, conv_session):
    """add_flagがTrueの場合、既存ドキュメントがあっても強制的に追加することを確認"""
    dummy_collection = _DummyCollection(uuid.uuid4())
    state = {"step": 0}

    async def side_effect(stmt):
        state["step"] += 1
        if state["step"] == 1:
            return _result_builder(value=dummy_collection)
        return _result_builder(scalar_value=2)

    conv_session.execute.side_effect = side_effect
    await conv_repo.add_document_to_collection(
        "pub_id", str(uuid.uuid4()), add_flag=True
    )
    conv_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_add_document_collection_not_found(conv_repo, conv_session):
    """存在しないコレクションに追加しようとした場合CollectionNotFoundErrorが発生することを確認"""

    async def side_effect(stmt):
        return _result_builder(value=None)

    conv_session.execute.side_effect = side_effect
    with pytest.raises(CollectionNotFoundError):
        await conv_repo.add_document_to_collection("missing", str(uuid.uuid4()))


@pytest.mark.asyncio
async def test_add_document_invalid_uuid(conv_repo, conv_session):
    """無効なUUID形式のドキュメントIDでDocumentUpdateErrorが発生することを確認"""
    dummy_collection = _DummyCollection(uuid.uuid4())

    async def side_effect(stmt):
        return _result_builder(value=dummy_collection, scalar_value=0)

    conv_session.execute.side_effect = side_effect
    with pytest.raises(DocumentUpdateError):
        await conv_repo.add_document_to_collection("pub", "NOT-UUID")


@pytest.mark.asyncio
async def test_add_document_sqlalchemy_error(conv_repo, conv_session):
    """SQLAlchemyError が add 時に発生した場合 DocumentUpdateError へラップされることを検証。

    既存テストは常に collection オブジェクトを返してしまい、"既存ドキュメント存在" 分岐で早期 return していたため
    session.add が呼ばれず期待する例外にならなかった。ここでは呼び出しシーケンスを制御する。
    1回目: コレクション取得 -> collection オブジェクト
    2回目: 既存ドキュメント取得 -> None （存在しない）
    3回目: position カウント -> 0
    その後 session.add で SQLAlchemyError を誘発し except SQLAlchemyError へ到達する。
    """
    dummy_collection = _DummyCollection(uuid.uuid4())
    state = {"step": 0}

    async def side_effect(stmt):
        state["step"] += 1
        if state["step"] == 1:  # collection fetch
            return _result_builder(value=dummy_collection)
        if state["step"] == 2:  # existing doc fetch -> None
            return _result_builder(value=None)
        return _result_builder(scalar_value=0)  # count

    conv_session.execute.side_effect = side_effect
    conv_session.add.side_effect = SQLAlchemyError("db error")
    with pytest.raises(DocumentUpdateError):
        await conv_repo.add_document_to_collection("pub", str(uuid.uuid4()))


@pytest.mark.asyncio
async def test_commit_success(conv_repo, conv_session):
    """commit成功時に正常に完了することを検証"""
    conv_session.commit = AsyncMock()
    await conv_repo.commit()
    conv_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_commit_error(conv_repo, conv_session):
    """commit時にSQLAlchemyErrorが発生した場合、DocumentUpdateErrorにラップされることを検証"""
    conv_session.commit.side_effect = SQLAlchemyError("commit failed")
    with pytest.raises(
        DocumentUpdateError, match="Failed to commit database transaction"
    ):
        await conv_repo.commit()


@pytest.mark.asyncio
async def test_rollback_success(conv_repo, conv_session):
    """rollback成功時に正常に完了することを検証"""
    conv_session.rollback = AsyncMock()
    await conv_repo.rollback()
    conv_session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_rollback_error(conv_repo, conv_session):
    """rollback時にSQLAlchemyErrorが発生した場合、DocumentUpdateErrorにラップされることを検証"""
    conv_session.rollback.side_effect = SQLAlchemyError("rollback failed")
    with pytest.raises(
        DocumentUpdateError, match="Failed to rollback database transaction"
    ):
        await conv_repo.rollback()
