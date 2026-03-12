from pydantic import BaseModel, Field
from typing_extensions import Literal

from qines_gai_backend.modules.documents.models import DocumentBase
from qines_gai_backend.schemas.schema import T_Artifact, T_Message


class Context(BaseModel):
    title: str = Field(
        ..., description="ドキュメントのタイトル", examples=["CAN Driver Specification"]
    )
    chunk: str = Field(
        ...,
        description="回答に使用された根拠となる情報",
        examples=["...このドキュメントではCAN Driverの仕様を記述..."],
    )
    path: str = Field(
        ...,
        description="ドキュメントのパス",
        examples=["/app/public/documents/R22-11/AUTOSAR_SWS_CANDriver.pdff"],
    )
    page: int = Field(..., description="`chunk`が含まれるページ番号", examples=[12])
    file_type: str = Field(
        ...,
        description="ドキュメントのMIMEタイプ",
        examples=["application/pdf"],
    )


class ArtifactBase(BaseModel):
    id: str = Field(
        ..., description="成果物のID", examples=["3a92c5d1-6f3b-4b9a-bc2c-9f7d6e4f8e7a"]
    )
    version: int = Field(..., description="成果物のバージョン", examples=[1])


class MessageMetadata(BaseModel):
    version: str = Field(
        "v1",
        description="メタデータのバージョン",
    )
    contexts: list[Context] | None = Field(
        None,
        description="回答に使用したコンテキスト",
    )
    recommended_documents: list[DocumentBase] | None = Field(
        None,
        description="レコメンドしたドキュメントの情報",
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
    generated_artifacts: list[ArtifactBase] | None = Field(
        None,
        description="このメッセージと一緒に生成された成果物のIDとバージョン",
        examples=[[{"id": "123e4567-e78b-3fea-15j6d93o931", "version": 1}]],
    )

    @classmethod
    def from_db(cls, message: T_Message) -> "MessageMetadata":
        # versionフィールドの構築
        if "version" in message.metadata_info and message.metadata_info["version"]:
            version = message.metadata_info["version"]
        else:
            version = "v1"

        # contextsフィールドの構築
        contexts = []
        if "contexts" in message.metadata_info and message.metadata_info["contexts"]:
            for context in message.metadata_info["contexts"]:
                contexts.append(
                    Context(
                        title=context["title"],
                        chunk=context["chunk"],
                        path=context["path"],
                        page=context["page"],
                        file_type=context["file_type"],
                    )
                )
        else:
            contexts = None

        # recommended_documentsフィールドの構築
        documents = []
        if (
            "recommended_documents" in message.metadata_info
            and message.metadata_info["recommended_documents"]
        ):
            for document in message.metadata_info["recommended_documents"]:
                documents.append(
                    DocumentBase(
                        id=document["id"],
                        title=document["title"],
                        path=document["path"],
                        subject=document["subject"],
                        genre=document.get("genre", None),
                        release=document.get("release", None),
                        file_type=document["file_type"],
                        summary=document.get("summary", ""),
                    )
                )
        else:
            documents = None

        # generated_artifactsフィールドの構築
        generated_artifacts = []
        if (
            "generated_artifacts" in message.metadata_info
            and message.metadata_info["generated_artifacts"]
        ):
            for generated_artifact in message.metadata_info["generated_artifacts"]:
                generated_artifacts.append(
                    ArtifactBase(
                        id=generated_artifact["id"],
                        version=generated_artifact["version"],
                    )
                )
        else:
            generated_artifacts = None

        return cls(
            version=version,
            contexts=contexts,
            recommended_documents=documents,
            generated_artifacts=generated_artifacts,
        )


# 会話内のメッセージ
class Message(BaseModel):
    role: Literal["user", "assistant"] = Field(
        ...,
        description="メッセージのロール(user/assistant)",
        examples=["assistant"],
    )
    content: str = Field(
        ...,
        description="メッセージの内容",
        examples=["CANドライバの初期化手順は、通常以下のようなステップで..."],
    )
    metadata: MessageMetadata = Field(..., description="メッセージに紐づくメタデータ")


class Artifact(ArtifactBase):
    title: str = Field(
        ..., description="成果物のタイトル", examples=["CANドライバの初期化手順"]
    )
    content: str = Field(
        ...,
        description="成果物の内容",
        examples=["CANドライバの初期化手順は、通常以下のようなステップで..."],
    )

    @classmethod
    def from_db(cls, artifact: T_Artifact) -> "Artifact":
        return cls(
            id=str(artifact.artifact_id),
            version=artifact.version,
            title=artifact.title,
            content=artifact.content,
        )


# 会話履歴一覧のレスポンス内のConversation
class ConversationBase(BaseModel):
    public_conversation_id: str = Field(
        ..., description="会話履歴の公開ID", examples=["Zf2k6A6R5h2"]
    )
    title: str = Field(
        ..., description="会話履歴のタイトル", examples=["CANドライバについて"]
    )


# 会話履歴のレスポンス
class ConversationDetail(ConversationBase):
    messages: list[Message] = Field(
        ...,
        description="会話履歴の中のメッセージのリスト",
        examples=[
            [
                {
                    "role": "user",
                    "content": "CANドライバの初期化手順はどのように定義されていますか？",
                    "metadata": {},
                },
                {
                    "role": "assistant",
                    "content": "CANドライバの初期化手順は、通常以下のようなステップで...",
                    "metadata": {
                        "contexts": [
                            {
                                "title": "Specification of CAN Driver",
                                "chunk": "...このドキュメントではCAN Driverの仕様を記述...",
                                "path": "/app/public/documents/R22-11/AUTOSAR_SWS_CANDriver.pdf",
                                "page": 12,
                                "file_type": "application/pdf",
                            }
                        ],
                        "recommended_documents": [
                            {
                                "id": "260ea4dd-36a7-401f-b2a1-d6a28d97f140",
                                "title": "Specification of CAN Driver",
                                "path": "/app/public/documents/R22-11/AUTOSAR_SWS_CANDriver.pdf",
                                "subject": "AUTOSAR",
                                "genre": "SWS",
                                "release": "R22-11",
                                "file_type": "application/pdf",
                            }
                        ],
                    },
                },
            ]
        ],
    )
    artifacts: list[Artifact] = Field(..., description="会話履歴に紐づく成果物のリスト")


class SharedConversation(BaseModel):
    url: str = Field(
        ...,
        description="発行された会話履歴共有用URL",
        examples=["http://qines-gai/share/conversations/V1StGXR8_Z5"],
    )
