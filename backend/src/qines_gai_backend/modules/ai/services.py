import json
from pathlib import Path
from typing import AsyncGenerator, List

import nanoid
from fastapi import HTTPException
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.ai.agents.init_collection_agent import (
    InitCollectionAgent,
)
from qines_gai_backend.modules.ai.agents.supervisor import Agent
from qines_gai_backend.modules.ai.llm_wrapper import LLMWrapper
from qines_gai_backend.modules.ai.models import (
    ChatCompletionsRequest,
    ChatRequestBase,
    StreamChat,
    Title,
)
from qines_gai_backend.modules.ai.repositories import AIRepository
from qines_gai_backend.modules.collections.models import CollectionDetail
from qines_gai_backend.modules.conversations.models import (
    Artifact,
    Message,
    MessageMetadata,
)
from qines_gai_backend.modules.documents.models import DocumentBase
from qines_gai_backend.shared.datetime_converter import convert_datetime_utc_to_jst
from qines_gai_backend.shared.document_access_checker import is_document_accesible
from qines_gai_backend.shared.exceptions import (
    CollectionCreationError,
)

logger = get_logger(__name__)


class AIService:
    """AI関連のビジネスロジック層

    AI機能のメインビジネスロジックを管理し、コレクション作成、
    チャットストリーミング、AIエージェントとの連携を提供します。
    """

    def __init__(self, repository: AIRepository):
        """AIServiceを初期化する

        Args:
            repository (AIRepository): AI関連のデータアクセスレポジトリ
        """
        self.repository = repository

    @log_function_start_end
    async def create_initial_collection(
        self,
        user_id: str,
        request: ChatRequestBase,
    ) -> CollectionDetail:
        """ユーザのリクエストに応じて初期コレクションを作成する

        ユーザーのメッセージに基づいてInitCollectionAgentを使用し、
        関連するドキュメントを検索して新しいコレクションを作成します。
        アクセス権限のチェックも実行します。

        Args:
            user_id (str): コレクションを作成するユーザーID
            request (ChatRequestBase): ユーザーのチャットリクエスト

        Returns:
            CollectionDetail: 作成されたコレクションの詳細情報

        Raises:
            CollectionCreationError: コレクション作成に失敗した場合
        """
        try:
            # エージェントの呼び出し
            init_collection_agent = InitCollectionAgent()
            response = await init_collection_agent.collection(
                self.repository.meili_client, request.message
            )
            response_dict = json.loads(response)
            document_ids = response_dict["document_ids"]
            collection_name = response_dict["name"]

            # ドキュメントアクセス権限チェック
            accessible_document_ids = []
            for document_id in document_ids:
                if await is_document_accesible(
                    self.repository.session, document_id, user_id
                ):
                    accessible_document_ids.append(document_id)

            # コレクション作成
            collection = await self.repository.create_collection(
                user_id=user_id,
                collection_name=collection_name,
                document_ids=accessible_document_ids,
            )

            # コミット前にデータ取得とPydanticモデル変換
            collection_detail = await self._build_collection_detail(collection)

            await self.repository.commit()
            return collection_detail

        except Exception as e:
            await self.repository.rollback()
            logger.error(f"Unexpected error: {str(e)}")
            raise CollectionCreationError("Failed to create initial collection")

    @log_function_start_end
    async def validate_stream_chat_request(
        self,
        user_id: str,
        request: ChatCompletionsRequest,
    ) -> None:
        """チャットリクエストの事前バリデーション"""
        # コレクション情報の取得
        collection_record = await self.repository.get_collection_by_public_id(
            request.public_collection_id
        )

        if not collection_record:
            logger.error("Collection not found")
            raise HTTPException(status_code=404, detail="Collection not found")

        if collection_record.user_id != user_id:
            logger.error("Not authorized to use this collection")
            raise HTTPException(
                status_code=403, detail="Not authorized to use this collection"
            )

        # 会話履歴の存在チェック（指定されている場合）
        if request.public_conversation_id:
            conversation_record = await self.repository.get_conversation_by_public_id(
                request.public_conversation_id
            )
            if not conversation_record:
                logger.error("Conversation not found")
                raise HTTPException(status_code=404, detail="Conversation not found")

    async def stream_chat(
        self,
        user_id: str,
        request: ChatCompletionsRequest,
    ) -> AsyncGenerator[str, None]:
        """ユーザーのリクエストに応じたチャットをストリーミングで返す

        指定されたコレクションと会話履歴を基にAIエージェントがチャットレスポンスを
        生成し、ストリーミングで配信します。メッセージとアーティファクトを
        データベースに保存します。

        Args:
            user_id (str): チャットを実行するユーザーID
            request (ChatCompletionsRequest): チャットリクエスト

        Yields:
            str: JSON形式のチャットレスポンスチャンク

        Raises:
            CollectionNotFoundError: コレクションが見つからない場合
            NotAuthorizedCollectionError: コレクションへのアクセス権限がない場合
            ConversationNotFoundError: 会話が見つからない場合
            ChatProcessingError: チャット処理に失敗した場合
        """
        try:
            # コレクション情報の取得（バリデーション済みなので存在確認のみ）
            collection_record = await self.repository.get_collection_by_public_id(
                request.public_collection_id, user_id
            )
            collection_detail = await self._build_collection_detail(collection_record)

            # 会話履歴と成果物の取得
            conversation_record = None
            messages = []
            artifacts = []

            if request.public_conversation_id:
                conversation_record = (
                    await self.repository.get_conversation_by_public_id(
                        request.public_conversation_id
                    )
                )

                # LangChainのメッセージ形式に変換
                for message in conversation_record.messages:
                    if message.sender_type == "user":
                        messages.append(HumanMessage(content=message.content))
                    else:
                        metadata = MessageMetadata(
                            version=message.metadata_info["version"],
                            contexts=message.metadata_info["contexts"],
                            recommended_documents=message.metadata_info[
                                "recommended_documents"
                            ],
                            generated_artifacts=message.metadata_info[
                                "generated_artifacts"
                            ],
                        )
                        content = f"{message.content}\n"
                        for artifact in metadata.generated_artifacts:
                            content += f"generated_artifact: {artifact.model_dump()}\n"
                        ai_message = AIMessage(content=content)
                        ai_message.additional_kwargs["qines_gai_metadata"] = (
                            metadata.model_dump()
                        )
                        messages.append(ai_message)

                artifacts = [
                    Artifact(
                        id=str(artifact.artifact_id),
                        title=artifact.title,
                        version=artifact.version,
                        content=artifact.content,
                    )
                    for artifact in conversation_record.artifacts
                ]

            messages.append(HumanMessage(content=request.message))

            # MCP設定ファイルのパス
            mcp_config_path = Path(__file__).parent / "mcp.json"

            # エージェントを作成（MCP接続も内部で行う）
            agent = await Agent.create(
                user_id=user_id,
                collection=collection_detail,
                mcp_config_path=mcp_config_path,
            )

            async for chunk in self._generate_and_save(
                agent,
                conversation_record,
                collection_record,
                messages,
                artifacts,
                request,
                user_id,
            ):
                yield chunk

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            yield json.dumps({"error": "Internal Server Error"}) + "\n"

    async def _generate_and_save(
        self,
        agent: Agent,
        conversation_record,
        collection_record,
        messages: List[BaseMessage],
        artifacts: List[Artifact],
        request: ChatCompletionsRequest,
        user_id: str,
    ) -> AsyncGenerator[str, None]:
        """チャット生成と保存処理

        AIエージェントからのレスポンスをストリーミングで取得し、
        同時にメッセージとアーティファクトをデータベースに保存します。

        Args:
            agent (Agent): AIエージェントインスタンス
            conversation_record: 会話レコード
            collection_record: コレクションレコード
            messages (List[BaseMessage]): 会話履歴のメッセージリスト
            artifacts (List[Artifact]): 既存のアーティファクトリスト
            request (ChatCompletionsRequest): チャットリクエスト
            user_id (str): ユーザーID

        Yields:
            str: ストリーミングレスポンスのJSON文字列
        """
        try:
            public_conversation_id = request.public_conversation_id
            if not public_conversation_id:
                public_conversation_id = nanoid.generate(size=11)

            async for msg in agent.astream(messages=messages, artifacts=artifacts):
                # レスポンス形式の構築
                response = StreamChat(
                    public_conversation_id=public_conversation_id,
                    message=Message(
                        role="assistant", content="", metadata=MessageMetadata()
                    ),
                )
                if msg.type == "message":
                    raw_metadata = msg.content.additional_kwargs.get(
                        "qines_gai_metadata"
                    )
                    if raw_metadata:
                        metadata = MessageMetadata.model_validate(raw_metadata)
                    else:
                        metadata = MessageMetadata()
                    response.message = Message(
                        role="assistant",
                        content=msg.content.content,
                        metadata=metadata,
                    )
                if msg.type == "artifact":
                    response.artifact = msg.content

                yield response.model_dump_json() + "\n"

            # 最終状態の取得と保存
            last_state = agent.get_state()

            # 会話の作成または更新
            if request.public_conversation_id:
                conversation_record = await self.repository.update_conversation(
                    conversation_record
                )
            else:
                # 新規の場合はタイトルを生成
                title = await self._generate_title(
                    request.message, last_state.messages[-1].content
                )
                conversation_record = await self.repository.create_conversation(
                    public_conversation_id=public_conversation_id,
                    user_id=user_id,
                    collection_id=collection_record.collection_id,
                    title=title,
                )

            # メッセージの保存
            await self.repository.create_message(
                conversation_id=conversation_record.conversation_id,
                sender_type="user",
                content=request.message,
                metadata_info={},
            )

            ai_message = await self.repository.create_message(
                conversation_id=conversation_record.conversation_id,
                sender_type="ai",
                content=last_state.messages[-1].content,
                metadata_info=last_state.messages[-1].additional_kwargs.get(
                    "qines_gai_metadata", MessageMetadata().model_dump()
                ),
            )

            # アーティファクトの保存
            await self.repository.session.refresh(conversation_record)
            if hasattr(last_state, "artifact_operations"):
                for operation in last_state.artifact_operations:
                    artifact = last_state.artifacts.get(operation.result)
                    if artifact is None:
                        logger.warning(
                            f"Artifact not found for operation result: {operation.result}"
                        )
                        continue
                    await self.repository.create_artifact(
                        artifact_id=artifact.id,
                        conversation_id=conversation_record.conversation_id,
                        message_id=ai_message.message_id,
                        title=artifact.title,
                        version=artifact.version,
                        content=artifact.content,
                    )

            # コレクションの使用時刻更新
            await self.repository.update_collection_used_at(
                collection_record.collection_id
            )

            await self.repository.commit()

        except Exception as e:
            await self.repository.rollback()
            logger.error(
                f"Unexpected error occurred in generate_and_save: {str(e)}",
                exc_info=True,
            )
            yield json.dumps({"error": "Internal Server Error"}) + "\n"

    async def _build_collection_detail(self, collection) -> CollectionDetail:
        """コレクション詳細情報を構築する

        データベースのコレクションオブジェクトからCollectionDetailモデルを構築します。
        関連するドキュメント情報も含めて変換します。

        Args:
            collection: データベースのコレクションオブジェクト

        Returns:
            CollectionDetail: コレクションの詳細情報
        """
        documents = [
            DocumentBase(
                id=str(doc.document.document_id),
                title=doc.document.file_name,
                path=doc.document.file_path,
                subject=doc.document.metadata_info.get("subject", "others"),
                genre=doc.document.metadata_info.get("genre"),
                release=doc.document.metadata_info.get("release"),
                file_type=doc.document.file_type,
                summary=doc.document.summary,
            )
            for doc in sorted(collection.collection_documents, key=lambda x: x.position)
        ]

        return CollectionDetail(
            public_collection_id=collection.public_collection_id,
            name=collection.name,
            documents=documents,
            created_at=convert_datetime_utc_to_jst(collection.created_at),
            updated_at=convert_datetime_utc_to_jst(collection.updated_at),
        )

    async def _generate_title(self, user_message: str, ai_response: str) -> str:
        """会話のタイトルを生成する

        ユーザーとAIの最初のやり取りから適切な会話タイトルを
        LLMを使用して生成します。

        Args:
            user_message (str): ユーザーのメッセージ
            ai_response (str): AIのレスポンス

        Returns:
            str: 生成されたタイトル（失敗時は"なし"）
        """
        instruction = f"""\
以下のユーザーとチャットボットの会話にわかりやすく、簡潔なタイトルをつけてください。
ユーザーの要望がひと目でわかるのが望ましいです。

ユーザー: {user_message}
チャットボット: {ai_response}

レスポンスは以下のJSONスキーマに従ってください。

```json_schema
{{
  "type": "object",
  "properties": {{
    "title": {{
      "type": "string"
    }}
  }},
  "required": ["title"],
  "additionalProperties": false
}}
```
        """

        try:
            wrapper = LLMWrapper()
            model = wrapper.get_structured_llm(Title, temperature=0)

            result = await model.ainvoke(instruction)
            logger.info(result)

            if isinstance(result, list):
                return result[0]
            elif isinstance(result, dict):
                return result.get("title", "なし")
            else:
                return "なし"
        except Exception as e:
            logger.error(f"Failed to generate title: {str(e)}")
            return "なし"
