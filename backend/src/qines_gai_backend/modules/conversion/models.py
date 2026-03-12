"""Update module Pydantic models

成果物更新処理に関するリクエスト・レスポンスモデルを定義します。
APIエンドポイントで使用されるデータ構造とバリデーションルールを提供します。

主なモデル:
- UpdateArtifactRequest: 成果物更新のリクエストデータ
- UpdateArtifactResponse: 成果物更新のレスポンスデータ
- DocumentUpdateInfo: 更新処理の詳細情報
"""

import uuid

from pydantic import BaseModel, Field


class UpdateDocumentRequest(BaseModel):
    """成果物更新のリクエストモデル。

    AIによって生成された成果物をドキュメントとして更新・登録するための
    リクエストパラメータです。公開コレクションID、成果物の一意識別子とバージョンを指定します。

    Attributes:
        public_collection_id: 公開コレクションの一意識別子（nanoid形式）
        artifact_id: 成果物の一意識別子（UUID形式）
        version: 成果物のバージョン番号（1以上の整数）
    """

    public_collection_id: str = Field(
        ...,
        description="公開コレクションの一意識別子（nanoid形式）",
        examples=["V1StGXR8_Z5"],
        min_length=11,
        max_length=11,
    )
    artifact_id: uuid.UUID = Field(
        ...,
        description="成果物の一意識別子（UUID形式）",
        examples=["3a92c5d1-6f3b-4b9a-bc2c-9f7d6e4f8e7a"],
    )
    version: int = Field(
        ..., description="成果物のバージョン番号（1以上）", examples=[1], ge=1
    )


class UpdateDocumentResponse(BaseModel):
    """成果物更新のレスポンスモデル。

    成果物のドキュメント更新処理の結果を返却します。
    処理の成功/失敗、更新されたドキュメントの情報、処理結果メッセージを含みます。

    Attributes:
        success: 更新処理が成功したかどうか
        message: 処理結果の説明メッセージ
        document_id: 更新後のドキュメントID（UUID形式）
        title: 更新されたドキュメントのタイトル
    """

    success: bool = Field(..., description="更新処理の成功/失敗フラグ", examples=[True])
    message: str = Field(
        ...,
        description="処理結果の詳細メッセージ",
        examples=["Document updated successfully"],
        min_length=1,
    )
    document_id: uuid.UUID = Field(
        ...,
        description="更新後のドキュメントの一意識別子（UUID形式）",
        examples=["260ea4dd-36a7-401f-b2a1-d6a28d97f140"],
    )
    title: str = Field(
        ...,
        description="更新されたドキュメントのタイトル",
        examples=["プレゼンテーション資料"],
        min_length=1,
        max_length=255,
    )


class DownloadArtifactRequest(BaseModel):
    """成果物ダウンロードのリクエストモデル"""

    artifact_id: str = Field(
        ..., description="成果物のID", examples=["3a92c5d1-6f3b-4b9a-bc2c-9f7d6e4f8e7a"]
    )
    version: int = Field(..., description="成果物のバージョン", examples=[1])


class AddDocumentRequest(BaseModel):
    """成果物新規追加のリクエストモデル。

    AIによって生成された成果物を新しいドキュメントとして追加するための
    リクエストパラメータです。公開コレクションID、成果物の一意識別子とバージョンを指定します。

    Attributes:
        public_collection_id: 公開コレクションの一意識別子（nanoid形式）
        artifact_id: 成果物の一意識別子（UUID形式）
        version: 成果物のバージョン番号（1以上の整数）
    """

    public_collection_id: str = Field(
        ...,
        description="公開コレクションの一意識別子（nanoid形式）",
        examples=["V1StGXR8_Z5"],
        min_length=11,
        max_length=11,
    )
    artifact_id: uuid.UUID = Field(
        ...,
        description="成果物の一意識別子（UUID形式）",
        examples=["3a92c5d1-6f3b-4b9a-bc2c-9f7d6e4f8e7a"],
    )
    version: int = Field(
        ..., description="成果物のバージョン番号（1以上）", examples=[1], ge=1
    )


class AddDocumentResponse(BaseModel):
    """成果物新規追加のレスポンスモデル。

    成果物のドキュメント新規追加処理の結果を返却します。
    処理の成功/失敗、追加されたドキュメントの情報、処理結果メッセージを含みます。

    Attributes:
        success: 新規追加処理が成功したかどうか
        message: 処理結果の説明メッセージ
        document_id: 追加後のドキュメントID（UUID形式）
        title: 追加されたドキュメントのタイトル
    """

    success: bool = Field(
        ..., description="新規追加処理の成功/失敗フラグ", examples=[True]
    )
    message: str = Field(
        ...,
        description="処理結果の詳細メッセージ",
        examples=["Document added successfully"],
        min_length=1,
    )
    document_id: uuid.UUID = Field(
        ...,
        description="追加後のドキュメントの一意識別子（UUID形式）",
        examples=["260ea4dd-36a7-401f-b2a1-d6a28d97f140"],
    )
    title: str = Field(
        ...,
        description="追加されたドキュメントのタイトル",
        examples=["プレゼンテーション資料"],
        min_length=1,
        max_length=255,
    )
