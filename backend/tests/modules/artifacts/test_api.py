import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException

from qines_gai_backend.modules.artifacts.services import ArtifactService
from qines_gai_backend.modules.artifacts.models import (
    EncodedArtifact,
    DownloadArtifactRequest,
)
from qines_gai_backend.shared.exceptions import ArtifactNotFoundError


class TestArtifactAPI:
    """Artifact APIのテストクラス"""

    @pytest.fixture
    def mock_artifact_service(self):
        """ArtifactServiceのモックを作成する"""
        return AsyncMock(spec=ArtifactService)

    @pytest.fixture
    def sample_encoded_artifact(self):
        """サンプルエンコード済み成果物データを作成する"""
        return EncodedArtifact(
            format="pptx",
            content="SGVsbG8gV29ybGQ=",  # "Hello World" in Base64
        )

    class TestDownloadArtifact:
        """download_artifact APIのテストクラス"""

        @pytest.mark.asyncio
        async def test_download_artifact_success(
            self, mock_artifact_service, sample_encoded_artifact
        ):
            """正常系：成果物のダウンロードが成功することを確認する"""
            # Arrange
            from qines_gai_backend.modules.artifacts.api import download_artifact

            format_param = "pptx"
            artifact_id = "3a92c5d1-6f3b-4b9a-bc2c-9f7d6e4f8e7a"
            version = 1

            mock_artifact_service.download_artifact.return_value = (
                sample_encoded_artifact
            )

            # Act
            result = await download_artifact(
                format=format_param,
                artifact_id=artifact_id,
                version=version,
                artifact_service=mock_artifact_service,
            )

            # Assert
            assert result == sample_encoded_artifact
            assert result.format == "pptx"
            assert result.content == "SGVsbG8gV29ybGQ="
            mock_artifact_service.download_artifact.assert_called_once()

            # 呼び出し引数の確認
            call_args = mock_artifact_service.download_artifact.call_args[0][0]
            assert call_args.format == format_param
            assert call_args.artifact_id == artifact_id
            assert call_args.version == version

        @pytest.mark.asyncio
        async def test_download_artifact_not_found(self, mock_artifact_service):
            """異常系：成果物が見つからない場合にHTTPException(404)が発生することを確認する"""
            # Arrange
            from qines_gai_backend.modules.artifacts.api import download_artifact

            format_param = "pptx"
            artifact_id = "nonexistent_id"
            version = 1

            mock_artifact_service.download_artifact.side_effect = ArtifactNotFoundError(
                "Artifact not found"
            )

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await download_artifact(
                    format=format_param,
                    artifact_id=artifact_id,
                    version=version,
                    artifact_service=mock_artifact_service,
                )

            assert exc_info.value.status_code == 404
            assert "Artifact not found" in str(exc_info.value.detail)

        @pytest.mark.asyncio
        async def test_download_artifact_internal_error(self, mock_artifact_service):
            """異常系：内部エラーの場合にHTTPException(500)が発生することを確認する"""
            # Arrange
            from qines_gai_backend.modules.artifacts.api import download_artifact

            format_param = "pptx"
            artifact_id = "test_artifact_id"
            version = 1

            mock_artifact_service.download_artifact.side_effect = Exception(
                "Database error"
            )

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await download_artifact(
                    format=format_param,
                    artifact_id=artifact_id,
                    version=version,
                    artifact_service=mock_artifact_service,
                )

            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Internal Server Error"

        @pytest.mark.asyncio
        async def test_download_artifact_with_different_format(
            self, mock_artifact_service
        ):
            """異なるフォーマットでの成果物ダウンロードを確認する"""
            # Arrange
            from qines_gai_backend.modules.artifacts.api import download_artifact

            format_param = "pdf"
            artifact_id = "test_artifact_id"
            version = 1

            pdf_artifact = EncodedArtifact(
                format="pdf", content="VGVzdCBQREYgQ29udGVudA=="
            )
            mock_artifact_service.download_artifact.return_value = pdf_artifact

            # Act
            result = await download_artifact(
                format=format_param,
                artifact_id=artifact_id,
                version=version,
                artifact_service=mock_artifact_service,
            )

            # Assert
            assert result.format == "pdf"
            assert result.content == "VGVzdCBQREYgQ29udGVudA=="

        @pytest.mark.asyncio
        async def test_download_artifact_with_different_version(
            self, mock_artifact_service, sample_encoded_artifact
        ):
            """異なるバージョンの成果物ダウンロードを確認する"""
            # Arrange
            from qines_gai_backend.modules.artifacts.api import download_artifact

            format_param = "pptx"
            artifact_id = "test_artifact_id"
            version = 5

            mock_artifact_service.download_artifact.return_value = (
                sample_encoded_artifact
            )

            # Act
            result = await download_artifact(
                format=format_param,
                artifact_id=artifact_id,
                version=version,
                artifact_service=mock_artifact_service,
            )

            # Assert
            assert result == sample_encoded_artifact

            # バージョン5が正しく渡されているか確認
            call_args = mock_artifact_service.download_artifact.call_args[0][0]
            assert call_args.version == version

        @pytest.mark.asyncio
        async def test_download_artifact_with_uuid_artifact_id(
            self, mock_artifact_service, sample_encoded_artifact
        ):
            """UUID形式のartifact_idでの成果物ダウンロードを確認する"""
            # Arrange
            from qines_gai_backend.modules.artifacts.api import download_artifact

            format_param = "pptx"
            artifact_id = "550e8400-e29b-41d4-a716-446655440000"
            version = 1

            mock_artifact_service.download_artifact.return_value = (
                sample_encoded_artifact
            )

            # Act
            result = await download_artifact(
                format=format_param,
                artifact_id=artifact_id,
                version=version,
                artifact_service=mock_artifact_service,
            )

            # Assert
            assert result == sample_encoded_artifact

            # UUID形式のartifact_idが正しく渡されているか確認
            call_args = mock_artifact_service.download_artifact.call_args[0][0]
            assert call_args.artifact_id == artifact_id

        @pytest.mark.asyncio
        async def test_download_artifact_with_version_one(
            self, mock_artifact_service, sample_encoded_artifact
        ):
            """バージョン1（初期バージョン）の成果物ダウンロードを確認する"""
            # Arrange
            from qines_gai_backend.modules.artifacts.api import download_artifact

            format_param = "pptx"
            artifact_id = "test_artifact_id"
            version = 1

            mock_artifact_service.download_artifact.return_value = (
                sample_encoded_artifact
            )

            # Act
            result = await download_artifact(
                format=format_param,
                artifact_id=artifact_id,
                version=version,
                artifact_service=mock_artifact_service,
            )

            # Assert
            assert result == sample_encoded_artifact
            mock_artifact_service.download_artifact.assert_called_once()

        @pytest.mark.asyncio
        async def test_download_artifact_service_exception_handling(
            self, mock_artifact_service
        ):
            """サービス層での例外が適切にHTTP例外に変換されることを確認する"""
            # Arrange
            from qines_gai_backend.modules.artifacts.api import download_artifact

            format_param = "pptx"
            artifact_id = "test_artifact_id"
            version = 1

            # サービス層で予期しない例外が発生
            mock_artifact_service.download_artifact.side_effect = ValueError(
                "Invalid data"
            )

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await download_artifact(
                    format=format_param,
                    artifact_id=artifact_id,
                    version=version,
                    artifact_service=mock_artifact_service,
                )

            # 500エラーが返されることを確認
            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Internal Server Error"

        @pytest.mark.asyncio
        async def test_download_artifact_request_validation(
            self, mock_artifact_service, sample_encoded_artifact
        ):
            """リクエストパラメータが正しくDownloadArtifactRequestに変換されることを確認する"""
            # Arrange
            from qines_gai_backend.modules.artifacts.api import download_artifact

            format_param = "pptx"
            artifact_id = "test_artifact_id"
            version = 2

            mock_artifact_service.download_artifact.return_value = (
                sample_encoded_artifact
            )

            # Act
            await download_artifact(
                format=format_param,
                artifact_id=artifact_id,
                version=version,
                artifact_service=mock_artifact_service,
            )

            # Assert
            # サービスに渡されたリクエストオブジェクトを確認
            call_args = mock_artifact_service.download_artifact.call_args[0][0]
            assert isinstance(call_args, DownloadArtifactRequest)
            assert call_args.format == format_param
            assert call_args.artifact_id == artifact_id
            assert call_args.version == version
