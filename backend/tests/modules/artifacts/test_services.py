import base64
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from qines_gai_backend.modules.artifacts.models import (
    DownloadArtifactRequest,
    EncodedArtifact,
    PowerPoint,
    TablePage,
    TableSection,
    TextPage,
    TextSection,
)
from qines_gai_backend.modules.artifacts.repositories import ArtifactRepository
from qines_gai_backend.modules.artifacts.services import ArtifactService
from qines_gai_backend.schemas.schema import T_Artifact
from qines_gai_backend.shared.exceptions import ArtifactNotFoundError


class TestArtifactService:
    """ArtifactServiceのテストクラス"""

    @pytest.fixture
    def mock_repository(self):
        """ArtifactRepositoryのモックを作成する"""
        return AsyncMock(spec=ArtifactRepository)

    @pytest.fixture
    def service(self, mock_repository):
        """ArtifactServiceのインスタンスを作成する"""
        return ArtifactService(mock_repository)

    @pytest.fixture
    def sample_artifact(self):
        """テスト用の成果物データを作成する"""
        mock_artifact = MagicMock(spec=T_Artifact)
        mock_artifact.artifact_id = "test_artifact_id"
        mock_artifact.conversation_id = "test_conversation_id"
        mock_artifact.title = "Test Presentation"
        mock_artifact.content = "# Test\n\nTest content"
        mock_artifact.version = 1
        return mock_artifact

    @pytest.fixture
    def sample_powerpoint(self):
        """テスト用のPowerPointデータを作成する"""
        return PowerPoint(
            title="Test Presentation",
            pages=[
                TextPage(
                    header="Test Header",
                    content="Test content",
                    template="text",
                    policy="Test policy",
                    sections=[
                        TextSection(title="Section 1", content=["Point 1", "Point 2"])
                    ],
                ),
                TablePage(
                    header="Table Header",
                    content="Table content",
                    template="table",
                    policy="Table policy",
                    table_section=TableSection(
                        title="Test Table", table_data=[["A", "B"], ["C", "D"]]
                    ),
                ),
            ],
        )

    @pytest.fixture
    def sample_request(self):
        """テスト用のダウンロードリクエストを作成する"""
        return DownloadArtifactRequest(
            format="pptx", artifact_id="test_artifact_id", version=1
        )

    class TestInit:
        """__init__メソッドのテストクラス"""

        def test_init_success(self, mock_repository):
            """初期化が正常に行われることを確認する"""
            # Act
            service = ArtifactService(mock_repository)

            # Assert
            assert service.repository is mock_repository

    class TestDownloadArtifact:
        """download_artifactメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_download_artifact_success(
            self,
            service,
            mock_repository,
            sample_artifact,
            sample_powerpoint,
            sample_request,
        ):
            """正常系：成果物のダウンロードが成功することを確認する"""
            # Arrange
            mock_repository.get_artifact_by_id_and_version.return_value = (
                sample_artifact
            )

            with (
                patch(
                    "qines_gai_backend.modules.artifacts.services.markdown_to_powerpoint"
                ) as mock_md_to_ppt,
                patch(
                    "qines_gai_backend.modules.artifacts.services.Presentation"
                ) as mock_presentation_class,
                patch(
                    "qines_gai_backend.modules.artifacts.services.TitleSlide"
                ) as mock_title_slide_class,
                patch(
                    "qines_gai_backend.modules.artifacts.services.TextSlide"
                ) as mock_text_slide_class,
                patch(
                    "qines_gai_backend.modules.artifacts.services.TableSlide"
                ) as mock_table_slide_class,
            ):
                mock_md_to_ppt.return_value = sample_powerpoint
                mock_prs = MagicMock()
                mock_prs.save = MagicMock()
                mock_prs.slide_layouts = MagicMock()
                mock_presentation_class.return_value = mock_prs

                # スライドのモックを設定
                mock_title_slide = MagicMock()
                mock_text_slide = MagicMock()
                mock_table_slide = MagicMock()

                mock_title_slide_class.return_value = mock_title_slide
                mock_text_slide_class.return_value = mock_text_slide
                mock_table_slide_class.return_value = mock_table_slide

                # BytesIOのモックを設定
                mock_binary_output = MagicMock(spec=io.BytesIO)
                mock_binary_output.read.return_value = b"test_pptx_data"
                mock_binary_output.getvalue.return_value = b"test_pptx_data"

                with patch(
                    "qines_gai_backend.modules.artifacts.services.io.BytesIO"
                ) as mock_bytesio:
                    mock_bytesio.return_value = mock_binary_output

                    # Act
                    result = await service.download_artifact(sample_request)

                    # Assert
                    assert isinstance(result, EncodedArtifact)
                    assert result.format == "pptx"
                    assert result.content == base64.b64encode(b"test_pptx_data").decode(
                        "utf-8"
                    )

                    mock_repository.get_artifact_by_id_and_version.assert_called_once_with(
                        "test_artifact_id", 1
                    )
                    mock_md_to_ppt.assert_called_once_with(sample_artifact.content)
                    mock_title_slide_class.assert_called_once()
                    mock_text_slide_class.assert_called_once()
                    mock_table_slide_class.assert_called_once()
                    mock_prs.save.assert_called_once_with(mock_binary_output)

        @pytest.mark.asyncio
        async def test_download_artifact_not_found(
            self, service, mock_repository, sample_request
        ):
            """異常系：成果物が見つからない場合の例外処理を確認する"""
            # Arrange
            mock_repository.get_artifact_by_id_and_version.return_value = None

            # Act & Assert
            with pytest.raises(ArtifactNotFoundError):
                await service.download_artifact(sample_request)

            mock_repository.get_artifact_by_id_and_version.assert_called_once_with(
                "test_artifact_id", 1
            )

        @pytest.mark.asyncio
        async def test_download_artifact_with_text_pages_only(
            self, service, mock_repository, sample_artifact, sample_request
        ):
            """テキストページのみの成果物をダウンロードする"""
            # Arrange
            mock_repository.get_artifact_by_id_and_version.return_value = (
                sample_artifact
            )

            text_only_powerpoint = PowerPoint(
                title="Text Only",
                pages=[
                    TextPage(
                        header="Header 1",
                        content="Content 1",
                        template="text",
                        policy="Policy",
                        sections=[TextSection(title="S1", content=["P1"])],
                    ),
                    TextPage(
                        header="Header 2",
                        content="Content 2",
                        template="text",
                        policy="Policy",
                        sections=[TextSection(title="S2", content=["P2"])],
                    ),
                ],
            )

            with (
                patch(
                    "qines_gai_backend.modules.artifacts.services.markdown_to_powerpoint"
                ) as mock_md_to_ppt,
                patch(
                    "qines_gai_backend.modules.artifacts.services.Presentation"
                ) as mock_presentation_class,
                patch(
                    "qines_gai_backend.modules.artifacts.services.TitleSlide"
                ) as mock_title_slide_class,
                patch(
                    "qines_gai_backend.modules.artifacts.services.TextSlide"
                ) as mock_text_slide_class,
            ):
                mock_md_to_ppt.return_value = text_only_powerpoint
                mock_prs = MagicMock()
                mock_prs.save = MagicMock()
                mock_prs.slide_layouts = MagicMock()
                mock_presentation_class.return_value = mock_prs

                mock_title_slide = MagicMock()
                mock_text_slide = MagicMock()

                mock_title_slide_class.return_value = mock_title_slide
                mock_text_slide_class.return_value = mock_text_slide

                mock_binary_output = MagicMock(spec=io.BytesIO)
                mock_binary_output.read.return_value = b"test_data"
                mock_binary_output.getvalue.return_value = b"test_data"

                with patch(
                    "qines_gai_backend.modules.artifacts.services.io.BytesIO"
                ) as mock_bytesio:
                    mock_bytesio.return_value = mock_binary_output

                    # Act
                    result = await service.download_artifact(sample_request)

                    # Assert
                    assert isinstance(result, EncodedArtifact)
                    assert mock_text_slide_class.call_count == 2

        @pytest.mark.asyncio
        async def test_download_artifact_with_table_pages_only(
            self, service, mock_repository, sample_artifact, sample_request
        ):
            """表ページのみの成果物をダウンロードする"""
            # Arrange
            mock_repository.get_artifact_by_id_and_version.return_value = (
                sample_artifact
            )

            table_only_powerpoint = PowerPoint(
                title="Table Only",
                pages=[
                    TablePage(
                        header="Table 1",
                        content="Content",
                        template="table",
                        policy="Policy",
                        table_section=TableSection(title="T1", table_data=[["A", "B"]]),
                    ),
                    TablePage(
                        header="Table 2",
                        content="Content",
                        template="table",
                        policy="Policy",
                        table_section=TableSection(title="T2", table_data=[["C", "D"]]),
                    ),
                ],
            )

            with (
                patch(
                    "qines_gai_backend.modules.artifacts.services.markdown_to_powerpoint"
                ) as mock_md_to_ppt,
                patch(
                    "qines_gai_backend.modules.artifacts.services.Presentation"
                ) as mock_presentation_class,
                patch(
                    "qines_gai_backend.modules.artifacts.services.TitleSlide"
                ) as mock_title_slide_class,
                patch(
                    "qines_gai_backend.modules.artifacts.services.TableSlide"
                ) as mock_table_slide_class,
            ):
                mock_md_to_ppt.return_value = table_only_powerpoint
                mock_prs = MagicMock()
                mock_prs.save = MagicMock()
                mock_prs.slide_layouts = MagicMock()
                mock_presentation_class.return_value = mock_prs

                mock_title_slide = MagicMock()
                mock_table_slide = MagicMock()

                mock_title_slide_class.return_value = mock_title_slide
                mock_table_slide_class.return_value = mock_table_slide

                mock_binary_output = MagicMock(spec=io.BytesIO)
                mock_binary_output.read.return_value = b"test_data"
                mock_binary_output.getvalue.return_value = b"test_data"

                with patch(
                    "qines_gai_backend.modules.artifacts.services.io.BytesIO"
                ) as mock_bytesio:
                    mock_bytesio.return_value = mock_binary_output

                    # Act
                    result = await service.download_artifact(sample_request)

                    # Assert
                    assert isinstance(result, EncodedArtifact)
                    assert mock_table_slide_class.call_count == 2

        @pytest.mark.asyncio
        async def test_download_artifact_conversion_error(
            self, service, mock_repository, sample_artifact, sample_request
        ):
            """異常系：PowerPoint変換エラーの場合の例外処理を確認する"""
            # Arrange
            mock_repository.get_artifact_by_id_and_version.return_value = (
                sample_artifact
            )

            with patch(
                "qines_gai_backend.modules.artifacts.services.markdown_to_powerpoint"
            ) as mock_md_to_ppt:
                mock_md_to_ppt.side_effect = Exception("Conversion error")

                # Act & Assert
                with pytest.raises(Exception) as exc_info:
                    await service.download_artifact(sample_request)

                assert "Conversion error" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_download_artifact_with_empty_pages(
            self, service, mock_repository, sample_artifact, sample_request
        ):
            """空のページリストを持つ成果物をダウンロードする"""
            # Arrange
            mock_repository.get_artifact_by_id_and_version.return_value = (
                sample_artifact
            )

            empty_powerpoint = PowerPoint(title="Empty", pages=[])

            with (
                patch(
                    "qines_gai_backend.modules.artifacts.services.markdown_to_powerpoint"
                ) as mock_md_to_ppt,
                patch(
                    "qines_gai_backend.modules.artifacts.services.Presentation"
                ) as mock_presentation_class,
                patch(
                    "qines_gai_backend.modules.artifacts.services.TitleSlide"
                ) as mock_title_slide_class,
            ):
                mock_md_to_ppt.return_value = empty_powerpoint
                mock_prs = MagicMock()
                mock_prs.save = MagicMock()
                mock_prs.slide_layouts = MagicMock()
                mock_presentation_class.return_value = mock_prs

                mock_title_slide = MagicMock()
                mock_title_slide_class.return_value = mock_title_slide

                mock_binary_output = MagicMock(spec=io.BytesIO)
                mock_binary_output.read.return_value = b"test_data"
                mock_binary_output.getvalue.return_value = b"test_data"

                with patch(
                    "qines_gai_backend.modules.artifacts.services.io.BytesIO"
                ) as mock_bytesio:
                    mock_bytesio.return_value = mock_binary_output

                    # Act
                    result = await service.download_artifact(sample_request)

                    # Assert
                    assert isinstance(result, EncodedArtifact)
                    mock_title_slide_class.assert_called_once()

        @pytest.mark.asyncio
        async def test_download_artifact_with_different_version(
            self, service, mock_repository, sample_artifact
        ):
            """異なるバージョンの成果物をダウンロードする"""
            # Arrange
            sample_artifact.version = 2
            mock_repository.get_artifact_by_id_and_version.return_value = (
                sample_artifact
            )

            request = DownloadArtifactRequest(
                format="pptx", artifact_id="test_artifact_id", version=2
            )

            with (
                patch(
                    "qines_gai_backend.modules.artifacts.services.markdown_to_powerpoint"
                ) as mock_md_to_ppt,
                patch(
                    "qines_gai_backend.modules.artifacts.services.Presentation"
                ) as mock_presentation_class,
                patch(
                    "qines_gai_backend.modules.artifacts.services.TitleSlide"
                ) as mock_title_slide_class,
            ):
                mock_md_to_ppt.return_value = PowerPoint(title="Test", pages=[])
                mock_prs = MagicMock()
                mock_prs.save = MagicMock()
                mock_prs.slide_layouts = MagicMock()
                mock_presentation_class.return_value = mock_prs

                mock_title_slide = MagicMock()
                mock_title_slide_class.return_value = mock_title_slide

                mock_binary_output = MagicMock(spec=io.BytesIO)
                mock_binary_output.read.return_value = b"test_data"
                mock_binary_output.getvalue.return_value = b"test_data"

                with patch(
                    "qines_gai_backend.modules.artifacts.services.io.BytesIO"
                ) as mock_bytesio:
                    mock_bytesio.return_value = mock_binary_output

                    # Act
                    result = await service.download_artifact(request)

                    # Assert
                    assert isinstance(result, EncodedArtifact)
                    mock_repository.get_artifact_by_id_and_version.assert_called_once_with(
                        "test_artifact_id", 2
                    )

        @pytest.mark.asyncio
        async def test_download_artifact_encoding_error(
            self,
            service,
            mock_repository,
            sample_artifact,
            sample_request,
            sample_powerpoint,
        ):
            """異常系：Base64エンコードエラーの場合の例外処理を確認する"""
            # Arrange
            mock_repository.get_artifact_by_id_and_version.return_value = (
                sample_artifact
            )

            with (
                patch(
                    "qines_gai_backend.modules.artifacts.services.markdown_to_powerpoint"
                ) as mock_md_to_ppt,
                patch(
                    "qines_gai_backend.modules.artifacts.services.Presentation"
                ) as mock_presentation_class,
                patch(
                    "qines_gai_backend.modules.artifacts.services.TitleSlide"
                ) as mock_title_slide_class,
            ):
                mock_md_to_ppt.return_value = sample_powerpoint
                mock_prs = MagicMock()
                mock_prs.save = MagicMock()
                mock_prs.slide_layouts = MagicMock()
                mock_presentation_class.return_value = mock_prs

                mock_title_slide = MagicMock()
                mock_title_slide_class.return_value = mock_title_slide

                with patch(
                    "qines_gai_backend.modules.artifacts.services.io.BytesIO"
                ) as mock_bytesio:
                    mock_bytesio.side_effect = Exception("Encoding error")

                    # Act & Assert
                    with pytest.raises(Exception) as exc_info:
                        await service.download_artifact(sample_request)

                    assert "Encoding error" in str(exc_info.value)
