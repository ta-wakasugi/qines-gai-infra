"""Artifacts module business logic layer"""

import base64
import io

from pptx import Presentation

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.ai.convert_md_to_pptx import markdown_to_powerpoint
from qines_gai_backend.modules.artifacts.models import (
    DownloadArtifactRequest,
    EncodedArtifact,
    TableSlide,
    TextSlide,
    TitleSlide,
)
from qines_gai_backend.modules.artifacts.repositories import ArtifactRepository
from qines_gai_backend.shared.exceptions import ArtifactNotFoundError

logger = get_logger(__name__)


class ArtifactService:
    """成果物関連のビジネスロジック層

    AIによって生成されたアーティファクトの処理を担当します。
    マークダウンコンテンツをPowerPointファイルに変換し、
    ダウンロード可能な形式で提供します。
    """

    def __init__(self, repository: ArtifactRepository):
        """ArtifactServiceを初期化する

        Args:
            repository (ArtifactRepository): 成果物関連のデータアクセスレポジトリ
        """
        self.repository = repository

    @log_function_start_end
    async def download_artifact(
        self, request: DownloadArtifactRequest
    ) -> EncodedArtifact:
        """成果物をダウンロード用にエンコードして返す

        指定されたアーティファクトをデータベースから取得し、
        マークダウンコンテンツをPowerPointプレゼンテーションに変換し、
        Base64エンコードした形式で返します。

        Args:
            request (DownloadArtifactRequest): ダウンロードリクエスト

        Returns:
            EncodedArtifact: Base64エンコードされた成果物データ

        Raises:
            ArtifactNotFoundError: 指定された成果物が見つからない場合
            Exception: PowerPoint変換やエンコードに失敗した場合
        """
        try:
            # 成果物を取得
            artifact = await self.repository.get_artifact_by_id_and_version(
                request.artifact_id, request.version
            )

            if not artifact:
                logger.error("Artifact not found")
                raise ArtifactNotFoundError("Artifact not found")

            # マークダウンをPowerPointオブジェクトに変換
            powerpoint = markdown_to_powerpoint(artifact.content)

            # PowerPointプレゼンテーションを作成
            prs = Presentation("pptx_template/SCSK_PPT_16x9_Design_A_jp.pptx")

            # タイトルスライドを作成
            slide_creator = TitleSlide(prs, artifact.title)
            slide_creator.create_slide()

            # コンテンツスライドを作成
            for page in powerpoint.pages:
                if page.template == "table":
                    slide_creator = TableSlide(prs, page)
                    slide_creator.create_slide()
                else:
                    slide_creator = TextSlide(prs, page)
                    slide_creator.create_slide()

            # メモリ上のバイトストリームにPowerPointプレゼンテーションを保存
            binary_output = io.BytesIO()
            prs.save(binary_output)
            binary_output.seek(0)

            # Base64エンコードでテキスト形式に変換
            content = base64.b64encode(binary_output.read()).decode("utf-8")

            # レスポンスデータを構築
            return EncodedArtifact(format=request.format, content=content)

        except ArtifactNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Internal Server Error: {str(e)}")
            raise
