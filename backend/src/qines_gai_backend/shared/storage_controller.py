from io import BytesIO

from mypy_boto3_s3 import S3Client

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.shared.exceptions import BaseAppError

logger = get_logger(__name__)


@log_function_start_end
async def upload_to_storage(
    file_content: bytes, bucket_name: str, s3_path: str, s3_client: S3Client
) -> str:
    """ファイルをS3にアップロードする。

    Args:
        file_content (bytes): アップロードするファイルのバイナリデータ
        bucket_name (str): S3バケット名
        s3_path (str): S3内の保存パス
        s3_client (S3Client): S3クライアント

    Returns:
        str: ファイルの保存パス

    Raises:
        BaseAppError: アップロードに失敗した場合
    """
    try:
        s3_client.upload_fileobj(
            BytesIO(file_content),
            bucket_name,
            s3_path,
        )
        return f"/{bucket_name}/{s3_path}"
    except Exception as e:
        logger.error(f"Failed to upload file to storage: {str(e)}")
        raise BaseAppError("Failed to upload file to storage")


@log_function_start_end
async def download_from_storage(s3_path: str, s3_client: S3Client) -> str:
    """ファイルをS3からダウンロードする。

    Args:
        s3_path (str): S3内の保存パス
        s3_client (S3Client): S3クライアント

    Returns:
        str: ファイルの中身

    Raises:
        BaseAppError: ダウンロードに失敗した場合
    """
    try:
        bucket_name, key = s3_path[1:].split("/", 1)
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        file_content = response["Body"].read().decode("utf-8")
        return file_content
    except Exception as e:
        logger.error(f"Failed to download file from storage: {str(e)}")
        raise BaseAppError("Failed to download file from storage")
