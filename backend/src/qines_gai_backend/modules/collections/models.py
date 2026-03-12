from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field

from qines_gai_backend.modules.documents.models import DocumentBase
from qines_gai_backend.schemas.schema import T_Collection, T_CollectionDocument
from qines_gai_backend.shared.byte_length_validater import validate_byte_length
from qines_gai_backend.shared.datetime_converter import convert_datetime_utc_to_jst


class CollectionBase(BaseModel):
    public_collection_id: str = Field(
        ..., description="公開コレクションID", examples=["V1StGXR8_Z5"]
    )
    name: str = Field(..., description="コレクション名", examples=["CAN仕様"])
    created_at: datetime = Field(
        ...,
        description="コレクションの作成日時",
        examples=["2023-05-16T14:30:45.123456+09:00"],
    )
    updated_at: datetime = Field(
        ...,
        description="コレクションの更新日時",
        examples=["2023-05-16T14:30:45.123456+09:00"],
    )

    @classmethod
    def from_db(cls, collection: T_Collection) -> "CollectionBase":
        """データベースレコードからCollectionBaseインスタンスを作成する"""
        return cls(
            public_collection_id=collection.public_collection_id,
            name=collection.name,
            created_at=convert_datetime_utc_to_jst(collection.created_at),
            updated_at=convert_datetime_utc_to_jst(collection.updated_at),
        )


class CollectionDetail(CollectionBase):
    documents: list[DocumentBase] = Field(
        ...,
        description="コレクションに含まれるドキュメントのリスト",
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
                }
            ]
        ],
    )

    @classmethod
    def from_db(
        cls, collection: T_Collection, collection_documents: list[T_CollectionDocument]
    ) -> "CollectionDetail":
        """データベースレコードからCollectionDetailインスタンスを作成する"""
        documents = [
            DocumentBase(
                id=str(collection_doc.document.document_id),
                title=collection_doc.document.file_name,
                path=collection_doc.document.file_path,
                subject=collection_doc.document.metadata_info.get("subject", "others"),
                genre=collection_doc.document.metadata_info.get("genre"),
                release=collection_doc.document.metadata_info.get("release"),
                file_type=collection_doc.document.file_type,
                summary=collection_doc.document.summary,
            )
            for collection_doc in sorted(
                collection_documents, key=lambda cd: cd.position
            )
        ]

        return cls(
            public_collection_id=collection.public_collection_id,
            name=collection.name,
            created_at=convert_datetime_utc_to_jst(collection.created_at),
            updated_at=convert_datetime_utc_to_jst(collection.updated_at),
            documents=documents,
        )


class CreateCollectionRequest(BaseModel):
    name: Annotated[
        str,
        Field(..., description="コレクション名", examples=["CAN仕様"]),
        AfterValidator(lambda v: validate_byte_length(v, 1, 100)),
    ]
    document_ids: list[UUID] = Field(
        ...,
        description="コレクションに含まれるドキュメントIDのリスト",
        examples=[
            [
                "260ea4dd-36a7-401f-b2a1-d6a28d97f140",
                "9188eea7-73a2-4045-84b9-c9d685d1184b",
            ]
        ],
    )


class RetrieveCollectionsResponse(BaseModel):
    total: int = Field(
        ..., description="ユーザーIDが一致しているレコードの件数", examples=[2]
    )
    offset: int = Field(..., description="データの取得開始位置", examples=[0])
    limit: int = Field(..., description="一度に取得するデータの最大数", examples=[10])
    collections: list[CollectionBase] = Field(
        ...,
        description="公開コレクションIDとコレクション名のリスト",
        examples=[
            [
                {
                    "public_collection_id": "V1StGXR8_Z5",
                    "name": "CAN仕様",
                    "created_at": "2023-05-16T14:30:45.123456+09:00",
                    "updated_at": "2023-05-16T14:30:45.123456+09:00",
                }
            ]
        ],
    )


class SharedCollection(BaseModel):
    url: str = Field(
        ...,
        description="発行されたコレクション共有用URL",
        examples=["http://qines-gai/share/collections/V1StGXR8_Z5"],
    )


class GetCollectionsRequest(BaseModel):
    offset: Annotated[
        int,
        Field(
            default=0,
            ge=0,
            description="データの取得開始位置(デフォルト:0)",
            examples=[0],
        ),
    ]
    limit: Annotated[
        int,
        Field(
            default=100,
            ge=0,
            description="一度に取得するデータの最大数(デフォルト:100)",
            examples=[100],
        ),
    ]
