"""Artifacts module API layer"""

from fastapi import APIRouter, Depends, HTTPException, Query

from qines_gai_backend.config.dependencies.services import get_artifact_service
from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.artifacts.models import (
    DownloadArtifactRequest,
    EncodedArtifact,
)
from qines_gai_backend.modules.artifacts.services import ArtifactService
from qines_gai_backend.shared.exceptions import ArtifactNotFoundError

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/api/artifacts/download",
    tags=["artifacts"],
    summary="A020:Download Artifact",
    operation_id="A020",
    response_model=EncodedArtifact,
    responses={
        404: {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "description": "Error detail message",
                            }
                        },
                        "required": ["detail"],
                    },
                    "examples": {
                        "not_found": {
                            "value": {"detail": "Artifact not found"}
                        }
                    },
                }
            },
        },
        500: {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "description": "Error detail message",
                            }
                        },
                        "required": ["detail"],
                    },
                    "examples": {
                        "internal_error": {
                            "value": {"detail": "Internal Server Error"}
                        }
                    },
                }
            },
        },
    },
)
@log_function_start_end
async def download_artifact(
    format: str = Query(
        ..., description="成果物のファイル形式(拡張子)", examples=["pptx"]
    ),
    artifact_id: str = Query(
        ..., description="成果物のID", examples=["3a92c5d1-6f3b-4b9a-bc2c-9f7d6e4f8e7a"]
    ),
    version: int = Query(..., description="成果物のバージョン", examples=[1]),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """成果物をダウンロード可能な形式で取得する

    指定されたアーティファクトIDとバージョンに基づいて成果物を取得し、
    マークダウン形式のコンテンツをPowerPointプレゼンテーションに変換して
    Base64エンコード形式で返します。

    Args:
        format (str): 成果物のファイル形式（拡張子）
        artifact_id (str): 成果物のID
        version (int): 成果物のバージョン番号
        artifact_service (ArtifactService): アーティファクトサービス

    Returns:
        EncodedArtifact: Base64エンコードされた成果物データ

    Raises:
        HTTPException: 以下の場合にHTTPExceptionが発生します：
            - 404: 指定された成果物が存在しない場合
            - 500: 内部サーバーエラーが発生した場合
    """
    try:
        request = DownloadArtifactRequest(
            format=format, artifact_id=artifact_id, version=version
        )

        return await artifact_service.download_artifact(request)

    except ArtifactNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
