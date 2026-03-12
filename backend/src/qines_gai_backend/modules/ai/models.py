from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict

from qines_gai_backend.modules.conversations.models import Artifact, Message


class TranslatedText(BaseModel):
    """翻訳結果のレスポンスモデル"""

    result: str = Field(
        ...,
        description="翻訳結果（日本語）",
        examples=["CANドライバの初期化手順は、通常以下のようなステップで..."],
    )


class TranslateTextRequest(BaseModel):
    """テキスト翻訳のリクエストモデル"""

    text: str = Field(
        ...,
        description="日本語に翻訳したいテキスト",
        examples=[
            "The initialization procedure for the CAN driver usually consists of the following steps..."
        ],
    )


class StreamChat(BaseModel):
    """チャット完了時のストリーミングレスポンスモデル"""

    public_conversation_id: str = Field(
        ..., description="会話履歴の公開ID", examples=["Zf2k6A6R5h2"]
    )
    message: Message = Field(
        ...,
        description="AIの返答内容",
    )
    artifact: Artifact | None = Field(None, description="チャットに紐づく成果物")


class ChatRequestBase(BaseModel):
    """チャットリクエストの基底クラス"""

    message: str = Field(
        ...,
        description="ユーザーの入力したAIへの要求内容",
        examples=["CANドライバの初期化手順はどのように定義されていますか？"],
    )


class ChatCompletionsRequest(ChatRequestBase):
    """チャット完了のリクエストモデル"""

    public_collection_id: str = Field(
        ..., description="公開コレクションID", examples=["V1StGXR8_Z5"]
    )
    public_conversation_id: str | None = Field(
        None, description="会話履歴の公開ID", examples=["Zf2k6A6R5h2"]
    )


class Title(TypedDict):
    """会話タイトル生成のためのスキーマ"""

    title: Annotated[str, ..., "簡潔でわかりやす会話履歴のタイトル"]
