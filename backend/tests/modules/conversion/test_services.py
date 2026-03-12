"""Conversionモジュールのサービスクラスのテスト

成果物からドキュメントへの変換処理におけるビジネスロジックを検証します。
Meilisearch登録、S3/ローカルストレージへの保存、データベーストランザクション、
各種エラーハンドリングなどを含みます。
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from qines_gai_backend.modules.conversion.services import ConversionService
from qines_gai_backend.modules.conversion.repositories import ConversionRepository
from qines_gai_backend.modules.documents.repositories import DocumentRepository
from qines_gai_backend.modules.artifacts.repositories import ArtifactRepository
from qines_gai_backend.shared.exceptions import (
    ArtifactNotFoundError,
    DocumentUpdateError,
)


@pytest.fixture
def repo():
    """ConversionRepositoryテスト用のモックを作成

    実際のMeilisearch AsyncClient.index(name)は同期関数でIndexオブジェクトを返し、
    その戻り値のメソッド(add_documents/delete_documents_by_filter)がawaitableです。
    ここではmeili_clientをMagicMockに変更し、index.return_valueのメソッドをAsyncMockにします。
    """
    r = AsyncMock(spec=ConversionRepository)
    r.commit = AsyncMock()
    r.rollback = AsyncMock()
    r.add_document_to_collection = AsyncMock()

    # Meilisearchクライアントモック構築
    index_obj = MagicMock()
    index_obj.add_documents = AsyncMock()
    index_obj.delete_documents_by_filter = AsyncMock(
        return_value=MagicMock(task_uid="1")
    )

    meili_client = MagicMock()
    meili_client.index.return_value = index_obj
    meili_client.wait_for_task = AsyncMock()
    r.meili_client = meili_client
    return r


@pytest.fixture
def document_repo():
    """DocumentRepositoryテスト用のモックを作成"""
    d = AsyncMock(spec=DocumentRepository)
    d.commit = AsyncMock()
    d.rollback = AsyncMock()
    d.get_document_by_id = AsyncMock()
    d.delete_document = AsyncMock()
    d.create_document = AsyncMock(return_value=MagicMock(file_path="/dummy/path"))
    return d


@pytest.fixture
def artifact_repo():
    """ArtifactRepositoryテスト用のモックを作成"""
    a = AsyncMock(spec=ArtifactRepository)
    a.commit = AsyncMock()
    a.rollback = AsyncMock()
    a.get_artifact_by_id_and_version = AsyncMock()
    return a


@pytest.fixture
def service(repo, document_repo, artifact_repo):
    """ConversionServiceインスタンスを作成"""
    return ConversionService(repo, document_repo, artifact_repo)


@pytest.fixture
def s3_client():
    """S3クライアントのモックを作成

    upload_fileobjは同期関数なのでMagicMockを使用
    """
    return MagicMock()


@pytest.mark.asyncio
async def test_add_document_from_artifact_success(
    service, repo, document_repo, artifact_repo, s3_client, monkeypatch
):
    """正常系：成果物から新規ドキュメント作成が成功することを確認

    - 成果物からタイトルとコンテンツを取得
    - S3へアップロード
    - Meilisearchへ登録
    - データベースコミット
    """
    artifact_repo.get_artifact_by_id_and_version.return_value = MagicMock(
        title="Title", content="Body"
    )
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket")

    async def fake_upload(data, bucket, path, client):
        return f"s3://{bucket}/{path}"

    monkeypatch.setattr(
        "qines_gai_backend.shared.storage_controller.upload_to_storage", fake_upload
    )

    result = await service.add_document_from_artifact(
        "pub_col", uuid.uuid4(), 1, "user1", s3_client
    )
    assert result["title"] == "Title"
    repo.add_document_to_collection.assert_awaited()
    document_repo.create_document.assert_awaited()
    repo.commit.assert_awaited()
    document_repo.commit.assert_awaited()


@pytest.mark.asyncio
async def test_add_document_from_artifact_artifact_not_found(
    service, repo, document_repo, artifact_repo, s3_client
):
    """異常系(ADD)：成果物が見つからない場合にArtifactNotFoundErrorが発生することを確認"""
    artifact_repo.get_artifact_by_id_and_version.return_value = None
    with pytest.raises(ArtifactNotFoundError):
        await service.add_document_from_artifact(
            "pub_col", uuid.uuid4(), 1, "user1", s3_client
        )
    repo.rollback.assert_awaited()
    document_repo.rollback.assert_awaited()


@pytest.mark.asyncio
async def test_add_document_from_artifact_empty_title(
    service, repo, document_repo, artifact_repo, s3_client
):
    """異常系(ADD)：タイトルが空の場合にDocumentUpdateErrorが発生することを確認"""
    artifact_repo.get_artifact_by_id_and_version.return_value = MagicMock(
        title="  ", content="body"
    )
    with pytest.raises(DocumentUpdateError):
        await service.add_document_from_artifact(
            "pub_col", uuid.uuid4(), 1, "user1", s3_client
        )


@pytest.mark.asyncio
async def test_add_document_from_artifact_empty_content(
    service, repo, document_repo, artifact_repo, s3_client
):
    """異常系(ADD)：コンテンツが空の場合にDocumentUpdateErrorが発生することを確認"""
    artifact_repo.get_artifact_by_id_and_version.return_value = MagicMock(
        title="Title", content="  "
    )
    with pytest.raises(DocumentUpdateError):
        await service.add_document_from_artifact(
            "pub_col", uuid.uuid4(), 1, "user1", s3_client
        )


@pytest.mark.asyncio
async def test_update_document_from_artifact_replace(
    service, repo, document_repo, artifact_repo, s3_client, monkeypatch
):
    """正常系(UPDATE)：既存ドキュメントを置換更新することを確認

    - Meilisearchから既存ドキュメントを削除
    - データベースから既存ドキュメントを削除
    - 新しいドキュメントを作成
    """
    artifact_id = uuid.uuid4()
    artifact_repo.get_artifact_by_id_and_version.return_value = MagicMock(
        title="Title", content="Content"
    )
    document_repo.get_document_by_id.return_value = MagicMock(document_id=artifact_id)
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket")

    async def fake_upload(data, bucket, path, client):
        return f"s3://{bucket}/{path}"

    monkeypatch.setattr(
        "qines_gai_backend.shared.storage_controller.upload_to_storage", fake_upload
    )

    await service.update_document_from_artifact(
        "pub_col", artifact_id, 1, "user1", s3_client
    )
    repo.meili_client.index.return_value.delete_documents_by_filter.assert_awaited()
    document_repo.delete_document.assert_awaited()
    document_repo.create_document.assert_awaited()
    repo.commit.assert_awaited()


@pytest.mark.asyncio
async def test_update_document_from_artifact_new_document(
    service, repo, document_repo, artifact_repo, s3_client, monkeypatch
):
    """正常系(UPDATE)：ドキュメントが存在しない場合に新規作成することを確認

    - get_document_by_idがNoneを返す
    - 削除処理がスキップされる
    - 新しいドキュメントが作成される
    """
    artifact_id = uuid.uuid4()
    artifact_repo.get_artifact_by_id_and_version.return_value = MagicMock(
        title="Title", content="Content"
    )
    document_repo.get_document_by_id.return_value = None
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket")

    async def fake_upload(data, bucket, path, client):
        return f"s3://{bucket}/{path}"

    monkeypatch.setattr(
        "qines_gai_backend.shared.storage_controller.upload_to_storage", fake_upload
    )

    result = await service.update_document_from_artifact(
        "pub_col", artifact_id, 1, "user1", s3_client
    )
    assert result["document_id"] == str(artifact_id)
    document_repo.delete_document.assert_not_called()


@pytest.mark.asyncio
async def test_update_document_from_artifact_artifact_not_found(
    service, repo, document_repo, artifact_repo, s3_client
):
    """異常系(UPDATE)：成果物が見つからない場合にArtifactNotFoundErrorが発生することを確認"""
    artifact_repo.get_artifact_by_id_and_version.return_value = None
    with pytest.raises(ArtifactNotFoundError):
        await service.update_document_from_artifact(
            "pub_col", uuid.uuid4(), 1, "user1", s3_client
        )
    repo.rollback.assert_awaited()
    document_repo.rollback.assert_awaited()


@pytest.mark.asyncio
async def test_update_document_from_artifact_empty_title(
    service, repo, document_repo, artifact_repo, s3_client
):
    """異常系(UPDATE)：タイトルが空の場合にDocumentUpdateErrorが発生することを確認"""
    artifact_repo.get_artifact_by_id_and_version.return_value = MagicMock(
        title="", content="body"
    )
    with pytest.raises(DocumentUpdateError):
        await service.update_document_from_artifact(
            "pub_col", uuid.uuid4(), 1, "user1", s3_client
        )


@pytest.mark.asyncio
async def test_update_document_from_artifact_empty_content(
    service, repo, document_repo, artifact_repo, s3_client
):
    """異常系(UPDATE)：コンテンツが空の場合にDocumentUpdateErrorが発生することを確認"""
    artifact_repo.get_artifact_by_id_and_version.return_value = MagicMock(
        title="Title", content=""
    )
    with pytest.raises(DocumentUpdateError):
        await service.update_document_from_artifact(
            "pub_col", uuid.uuid4(), 1, "user1", s3_client
        )


@pytest.mark.asyncio
async def test_update_document_from_artifact_unexpected_error(
    service, repo, document_repo, artifact_repo, s3_client, monkeypatch
):
    """異常系(UPDATE)：予期しない例外が発生した場合にDocumentUpdateErrorでラップされることを確認

    - データベース操作で予期しない例外発生
    - DocumentUpdateErrorにラップされて再送出
    - ロールバック処理が実行される
    """
    artifact_repo.get_artifact_by_id_and_version.return_value = MagicMock(
        title="Title", content="Body"
    )
    document_repo.get_document_by_id.side_effect = Exception("boom")
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket")

    async def fake_upload(data, bucket, path, client):
        return f"s3://{bucket}/{path}"

    monkeypatch.setattr(
        "qines_gai_backend.shared.storage_controller.upload_to_storage", fake_upload
    )
    with pytest.raises(DocumentUpdateError):
        await service.update_document_from_artifact(
            "pub_col", uuid.uuid4(), 1, "user1", s3_client
        )
    repo.rollback.assert_awaited()
    document_repo.rollback.assert_awaited()


# === Additional service failure/branch coverage tests ===


@pytest.mark.asyncio
async def test_save_to_s3_s3_missing_bucket_error(service, artifact_repo, monkeypatch):
    """異常系(S3保存)：S3_BUCKET_NAMEが設定されていない場合にDocumentUpdateErrorが発生することを確認"""
    artifact_repo.get_artifact_by_id_and_version.return_value = MagicMock(
        title="T", content="C"
    )
    monkeypatch.delenv("SAVE_LOCALLY", raising=False)
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
    s3_client = MagicMock()
    with pytest.raises(DocumentUpdateError):
        await service.add_document_from_artifact(
            "pub_col", uuid.uuid4(), 1, "user1", s3_client
        )


@pytest.mark.asyncio
async def test_save_to_s3_s3_upload_success(
    service, artifact_repo, document_repo, repo, monkeypatch
):
    """正常系(S3保存)：S3へのアップロードが成功することを確認

    - S3クライアントのupload_fileobjが呼ばれる
    - ドキュメント作成処理が完了する
    """

    artifact_repo.get_artifact_by_id_and_version.return_value = MagicMock(
        title="S3Title", content="S3Content"
    )
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    monkeypatch.delenv("SAVE_LOCALLY", raising=False)

    # S3クライアントのモック
    s3_client = MagicMock()
    s3_client.upload_fileobj = MagicMock()

    result = await service.add_document_from_artifact(
        "pub_col", uuid.uuid4(), 1, "user1", s3_client
    )

    # S3アップロードが呼ばれたことを確認
    assert s3_client.upload_fileobj.called
    assert result["title"] == "S3Title"


@pytest.mark.asyncio
async def test_register_as_document_meilisearch_add_fail(
    service, repo, artifact_repo, monkeypatch
):
    """異常系(Meilisearch登録)：Meilisearch登録失敗時にDocumentUpdateErrorが発生することを確認"""
    artifact_repo.get_artifact_by_id_and_version.return_value = MagicMock(
        title="T", content="C"
    )
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket")
    # Force Meilisearch add_documents failure
    repo.meili_client.index.return_value.add_documents.side_effect = Exception(
        "add fail"
    )
    s3_client = MagicMock()
    with pytest.raises(DocumentUpdateError):
        await service.add_document_from_artifact(
            "pub_col", uuid.uuid4(), 1, "user1", s3_client
        )


@pytest.mark.asyncio
async def test_delete_from_meilisearch_fail(
    service, repo, document_repo, artifact_repo, monkeypatch
):
    """異常系(Meilisearch削除)：Meilisearchからの削除失敗時にDocumentUpdateErrorが発生することを確認"""
    artifact_id = uuid.uuid4()
    artifact_repo.get_artifact_by_id_and_version.return_value = MagicMock(
        title="T", content="C"
    )
    document_repo.get_document_by_id.return_value = MagicMock(document_id=artifact_id)
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket")
    # Simulate delete failure
    repo.meili_client.index.return_value.delete_documents_by_filter.side_effect = (
        Exception("del fail")
    )
    s3_client = MagicMock()
    with pytest.raises(DocumentUpdateError):
        await service.update_document_from_artifact(
            "pub_col", artifact_id, 1, "user1", s3_client
        )


@pytest.mark.asyncio
async def test_add_document_unexpected_error(service, repo, artifact_repo, monkeypatch):
    """異常系(ADD)：save_to_s3後の予期しない例外がDocumentUpdateErrorでラップされることを確認

    - add_document_to_collectionで例外発生
    - DocumentUpdateErrorでラップされて再送出
    """
    # Trigger unexpected error after save_to_s3 by failing add_document_to_collection
    artifact_repo.get_artifact_by_id_and_version.return_value = MagicMock(
        title="T", content="C"
    )
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket")
    repo.add_document_to_collection.side_effect = RuntimeError("boom")
    s3_client = MagicMock()
    with pytest.raises(DocumentUpdateError):
        await service.add_document_from_artifact(
            "pub_col", uuid.uuid4(), 1, "user1", s3_client
        )
