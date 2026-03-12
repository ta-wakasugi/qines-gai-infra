from typing import Any, List, Optional

from pydantic import BaseModel, Field
from typing_extensions import Literal

from qines_gai_backend.schemas.schema import T_Document


class DocumentBase(BaseModel):
    """ドキュメントの基本情報"""

    id: str = Field(
        ...,
        description="ドキュメントID",
        examples=["260ea4dd-36a7-401f-b2a1-d6a28d97f140"],
    )
    title: str = Field(
        ...,
        description="ドキュメントのタイトル",
        examples=["Specification of CAN Driver"],
    )
    path: str = Field(
        ...,
        description="ドキュメントのパス",
        examples=["/app/public/documents/R22-11/AUTOSAR_SWS_CANDriver.pdf"],
    )
    subject: Literal["AUTOSAR", "others"] = Field(
        ..., description="ドキュメントの種類", examples=["AUTOSAR"]
    )
    genre: Optional[str] = Field(
        None, description="AUTOSARドキュメントのワーキンググループ", examples=["SWS"]
    )
    release: Optional[str] = Field(
        None, description="AUTOSARドキュメントのリリースバージョン", examples=["R22-11"]
    )
    file_type: str = Field(
        ...,
        description="ドキュメントのMIMEタイプ",
        examples=["application/pdf"],
    )
    summary: str = Field(
        default="",
        description="ドキュメントの要約",
        examples=["This document describes the CAN driver specification..."],
    )

    @classmethod
    def from_db(cls, document: T_Document) -> "DocumentBase":
        """データベースエンティティからPydanticモデルに変換"""
        metadata = document.metadata_info or {}
        return cls(
            id=str(document.document_id),
            title=document.file_name,
            path=document.file_path,
            subject=metadata.get("subject", "others"),
            genre=metadata.get("genre"),
            release=metadata.get("release"),
            file_type=document.file_type,
            summary=document.summary,
        )


class SearchDocumentsRequest(BaseModel):
    """ドキュメント検索リクエスト"""

    q: Optional[str] = Field(None, description="検索クエリ", examples=["CAN driver"])
    hits_per_page: int = Field(
        default=7, description="1ページに含める検索結果の数", examples=[7]
    )
    page: int = Field(default=1, description="取得したいページ番号", examples=[1])
    uploader: Optional[List[Literal["user", "admin"]]] = Field(
        default=["user", "admin"],
        description="ドキュメントのアップロード者",
        examples=[["admin"]],
    )
    genre: Optional[str] = Field(
        None,
        description="AUTOSARドキュメントのワーキンググループ",
        examples=["SWS,EXP"],
    )
    release: Optional[str] = Field(
        None,
        description="AUTOSARドキュメントのリリースバージョン",
        examples=["R4-2-2"],
    )


class SearchDocumentsResponse(BaseModel):
    """ドキュメント検索レスポンス"""

    total_pages: int = Field(..., description="検索結果のページ総数", examples=[3])
    documents: List[DocumentBase] = Field(
        ...,
        description="検索結果のリスト",
        examples=[
            [
                {
                    "id": "260ea4dd-36a7-401f-b2a1-d6a28d97f140",
                    "title": "Specification of CAN Driver",
                    "path": "/app/public/documents/R22-11/AUTOSAR_SWS_CANDriver.pdf",
                    "subject": "AUTOSAR",
                    "genre": "SWS",
                    "release": "R22-11",
                    "file_type": "application/pdf",
                },
            ]
        ],
    )


class UploadDocumentRequest(BaseModel):
    """ドキュメントアップロードリクエスト（メタデータ）"""

    subject: Literal["AUTOSAR", "others"] = Field(
        default="others", description="ドキュメントの種類"
    )
    genre: Optional[str] = Field(
        None, description="AUTOSARドキュメントのワーキンググループ"
    )
    release: Optional[str] = Field(
        None, description="AUTOSARドキュメントのリリースバージョン"
    )


class MeilisearchChunk(BaseModel):
    """Meilisearchのチャンク情報"""

    id: str
    doc_id: str
    title: str
    total_pages: int
    page_num: int
    chunk_num: int
    contents: str
    subject: Literal["AUTOSAR", "others"]
    path: str
    uploader: str
    file_type: str
    genre: str | None = None
    release: str | None = None
    _formatted: dict[str, Any] | None
