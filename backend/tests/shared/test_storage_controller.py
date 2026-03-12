import pytest
from unittest.mock import MagicMock
from io import BytesIO

from qines_gai_backend.shared.storage_controller import (
    upload_to_storage,
    download_from_storage,
)
from qines_gai_backend.shared.exceptions import BaseAppError

# テスト用のコンテンツ
TEST_CONTENT_BYTES = b"this is a test content"
TEST_CONTENT_STR = "this is a test content"
BUCKET_NAME = "test-bucket"
S3_PATH = "test/path/file.txt"
FULL_S3_PATH = f"/{BUCKET_NAME}/{S3_PATH}"


@pytest.mark.asyncio
async def test_upload_to_storage_s3():
    """
    upload_to_storage: S3へのアップロードテスト
    """
    mock_s3_client = MagicMock()
    mock_s3_client.upload_fileobj = MagicMock()

    result_path = await upload_to_storage(
        TEST_CONTENT_BYTES, BUCKET_NAME, S3_PATH, mock_s3_client
    )

    # 結果を検証
    assert result_path == FULL_S3_PATH
    # upload_fileobjが正しく呼び出されたか確認
    mock_s3_client.upload_fileobj.assert_called_once()
    # 第1引数(BytesIO)の内容を検証
    call_args = mock_s3_client.upload_fileobj.call_args[0]
    assert call_args[0].read() == TEST_CONTENT_BYTES
    assert call_args[1] == BUCKET_NAME
    assert call_args[2] == S3_PATH


@pytest.mark.asyncio
async def test_download_from_storage_s3():
    """
    download_from_storage: S3からのダウンロードテスト
    """
    mock_s3_client = MagicMock()
    # get_objectの戻り値を設定
    mock_s3_client.get_object.return_value = {"Body": BytesIO(TEST_CONTENT_BYTES)}

    content = await download_from_storage(FULL_S3_PATH, mock_s3_client)

    # 結果を検証
    assert content == TEST_CONTENT_STR
    mock_s3_client.get_object.assert_called_once_with(
        Bucket=BUCKET_NAME, Key=S3_PATH
    )


@pytest.mark.asyncio
async def test_upload_to_storage_exception():
    """
    upload_to_storage: 例外発生時のテスト
    """
    mock_s3_client = MagicMock()
    mock_s3_client.upload_fileobj.side_effect = Exception("S3 upload error")

    with pytest.raises(BaseAppError, match="Failed to upload file to storage"):
        await upload_to_storage(
            TEST_CONTENT_BYTES, BUCKET_NAME, S3_PATH, mock_s3_client
        )


@pytest.mark.asyncio
async def test_download_from_storage_exception():
    """
    download_from_storage: 例外発生時のテスト
    """
    mock_s3_client = MagicMock()
    mock_s3_client.get_object.side_effect = Exception("S3 download error")

    with pytest.raises(BaseAppError, match="Failed to download file from storage"):
        await download_from_storage(FULL_S3_PATH, mock_s3_client)
