import json
import os

import nanoid
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
)
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from langfuse.callback import CallbackHandler
from langgraph.graph import END, START
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.ai.llm_wrapper import LLMWrapper
from qines_gai_backend.modules.ai.tools import get_adj_chunk, search_on_meilisearch
from qines_gai_backend.modules.conversations.models import Context
from qines_gai_backend.modules.documents.models import DocumentBase

logger = get_logger(__file__)


RESEACHER_PROMPT = """\
あなたは、以下「対応すべきの目標」を達成するために、検索エンジンから情報を収集し、統合するAIアシスタントです。検索結果を分析し、目標に直接関連する簡潔で適切な回答を提供してください。

## 対応すべき目標

{goal}

## 回答を作成する際の手順

- すべての検索結果を注意深く読む。
- 目標に直接関連する情報を特定する。
- 重要かつ信頼性の高い情報を優先する。
- 関連情報を統合し、一貫した回答を作成する。
- 目標に対して的確な回答を提供する。
- 見つからない場合は再検索する。

## 回答の作成方針:

- 簡潔かつ的確にまとめる。
- 明確で分かりやすい言葉を使用する。
- 論理的に整理する。
- 必要に応じて、箇条書きや番号リストを活用する。
- 規定回数検索しても見つからない場合や、結果に情報が含まれていない場合は、絶対に自分の知識で推測せず、「提供されたドキュメントの中に該当する情報が見つかりませんでした」と回答してください。
"""

GRADE_PROMPT = """\
あなたは文書の採点者です。以下、対応すべき目標と、そのために集めたドキュメント群を示します。

対応すべき目標: {goal}

集めたドキュメント群:
{documents}

ドキュメント群の中で、目標達成のために必須であると考えられるドキュメントのIDをJSON形式で出力して下さい。
ドキュメントのIDとは検索結果のJSONに含まれる'id'キーの値のことです。
```json
{{
    "useful_docs": ["document-id1", "document-id2"],
}}
```
"""


class RelevantDocuments(BaseModel):
    useful_docs: list[str] = Field(
        [], description="目標達成に必要なドキュメントのIDのリスト"
    )


class ResearcherState(BaseModel):
    goal: str = Field(..., description="調査によって達成したい目標")
    messages: Annotated[list[BaseMessage], add_messages] = Field(
        ..., description="エージェントの行動履歴"
    )
    remaining_tool_call: int = Field(10, description="ツールの残りの実行回数")
    contexts: list[Context] = Field(
        [], description="調査によって得られた目標を達成するために必要な文献"
    )
    recommendations: list[DocumentBase] | None = Field(
        None, description="優先検索対象外にあるが、有用な文献"
    )


# langgraph.prebuilt.create_react_agentをベースに、ツールの実行回数制限と、レコメンド機能を導入
# TODO: ReWOOやReflectionで精度が上がるか検証
class Researcher:
    @log_function_start_end
    def __init__(
        self,
        llm: BaseChatModel,
        documents: list[DocumentBase],
        config: RunnableConfig,
    ):
        """文献調査を行うエージェント

        Args:
            llm: エージェントに使用するモデル
            documents: アクセス可能なドキュメント群
        """
        self._llm = llm
        self._documents = documents

        self._config = config

        user_id = config["configurable"].get("user_id")
        if not user_id:
            raise ValueError("ユーザーIDがありません。フィルターの構成に失敗しました。")
        self._base_filter = [f"uploader IN [{user_id}, admin]"]

        load_dotenv("/app/.env")
        USE_LANGFUSE = os.getenv("USE_LANGFUSE", "false")
        langfuse_handler = CallbackHandler(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
            user_id=os.getenv("LANGFUSE_USER_ID"),
        )
        USE_LANGFUSE = USE_LANGFUSE == "true"
        self._config["callbacks"] = [langfuse_handler] if USE_LANGFUSE else []

        self._workflow = self._build_graph()

    @log_function_start_end
    def _build_graph(self) -> CompiledStateGraph:
        """エージェントのワークフローを初期化する"""
        graph = StateGraph(ResearcherState)
        graph.add_node("agent", self._agent)
        graph.add_node("research", self._research)
        # graph.add_node("recommend", self._recommend)
        graph.add_edge(START, "agent")
        graph.add_conditional_edges("agent", self._should_continue)
        graph.add_edge("research", "agent")
        # graph.add_edge("recommend", END)

        return graph.compile()

    # Node Functions
    @log_function_start_end
    async def _agent(self, state: ResearcherState, config: RunnableConfig):
        prompt = ChatPromptTemplate(
            [
                ("system", RESEACHER_PROMPT),
                ("placeholder", "{messages}"),
            ]
        )
        chain = prompt | self._llm.bind_tools([search_on_meilisearch, get_adj_chunk])

        response = await chain.ainvoke(
            {"goal": state.goal, "messages": state.messages}, config=config
        )
        return {"messages": [response]}

    @log_function_start_end
    async def _research(self, state: ResearcherState, config: RunnableConfig):
        results = []
        contexts = state.contexts

        # 検索範囲をコレクション内に限定するフィルター
        filter = self._base_filter + [
            "doc_id IN [" + ",".join([d.id for d in self._documents]) + "]"
        ]

        # TODO: langgraph.prebuilt.ToolNodeのように非同期で複数のツールを呼び出す
        for tool_call in state.messages[-1].tool_calls:
            if tool_call["name"] == "search_on_meilisearch":
                tool_call["args"]["filter"] = filter
                result: ToolMessage = await search_on_meilisearch.ainvoke(tool_call)
                grade_result = await self._grade_documents(state.goal, result.content)

                refined_tool_message_contents = []
                for meili_doc in result.artifact:
                    if meili_doc["id"] in grade_result.useful_docs:
                        refined_tool_message_contents.append(meili_doc)
                        # contents の真ん中の300文字だけ返す
                        contents = meili_doc["contents"]
                        if len(contents) > 1000:
                            start = (len(contents) - 300) // 2
                            middle = contents[start : start + 300]
                            contents = f"... {middle} ..."
                        contexts.append(
                            Context(
                                title=meili_doc["title"],
                                chunk=contents,
                                page=meili_doc["page_num"],
                                path=meili_doc["path"],
                                file_type=meili_doc["file_type"],
                            )
                        )
                # AIMessageのtool_callsの各要素の`id`に対応したToolMessageがstate.messages内に
                # 存在しないといけないため、`_grade_documents`で有用な結果がなかったときは、その旨をToolMessageにする
                if len(refined_tool_message_contents) == 0:
                    content = "ゴール達成に有用な情報が見つかりませんでした。クエリを変えてください。"
                else:
                    content = json.dumps(
                        refined_tool_message_contents, ensure_ascii=False, indent=2
                    )
                results.append(
                    ToolMessage(content=content, tool_call_id=tool_call["id"])
                )
            else:
                results.append(await get_adj_chunk.ainvoke(tool_call))

        return {
            "messages": results,
            "remaining_tool_call": state.remaining_tool_call - 1,
            "contexts": contexts,
        }

    @log_function_start_end
    async def _recommend(self, state: ResearcherState, config: RunnableConfig):
        # 最後に使用したクエリを再利用
        last_query = None
        for msg in reversed(state.messages):
            if isinstance(msg, AIMessage):
                tool_call_args = msg.tool_calls[-1]["args"]
                last_query = tool_call_args.get("query")

        if not last_query:
            return {"recommendations": None}

        # 検索範囲をコレクション外に限定するフィルター
        filter = self._base_filter + [
            "doc_id NOT IN [" + ",".join([d.id for d in self._documents]) + "]"
        ]
        # artifactsを得るためにToolCallとしてツールを呼び出す
        # ref: https://python.langchain.com/docs/how_to/tool_artifacts/#invoking-the-tool-with-toolcall
        tool_call = {
            "name": "search_on_meilisearch",
            "id": "call_" + nanoid.generate(size=24),  # この値はなんでも可
            "type": "tool_call",
            "args": {"query": last_query, "filter": filter},
        }

        result: ToolMessage = await search_on_meilisearch.ainvoke(tool_call)
        grade_result = await self._grade_documents(state.goal, result.content)

        # 同じファイルをレコメンドしないように
        # Meilisearchに登録してあるdoc_idごとにmodels.documents.Documentを作成
        recommended_documents = {}
        for meili_doc in result.artifact:
            if (
                meili_doc["id"] in grade_result.useful_docs
                and meili_doc["doc_id"] not in recommended_documents
            ):
                recommended_documents[meili_doc["doc_id"]] = DocumentBase(
                    id=meili_doc["doc_id"],
                    title=meili_doc["title"],
                    path=meili_doc["path"],
                    subject=meili_doc["subject"],
                    genre=(
                        meili_doc["genre"]
                        if meili_doc["subject"] == "AUTOSAR"
                        else None
                    ),
                    release=(
                        meili_doc["release"]
                        if meili_doc["subject"] == "AUTOSAR"
                        else None
                    ),
                    file_type=meili_doc["file_type"],
                )

        return {"recommendations": list(recommended_documents.values())}

    # Node Util Funtion
    @log_function_start_end
    async def _grade_documents(self, goal: str, documents: str) -> RelevantDocuments:
        """検索で得られたドキュメントを評価する

        Args:
            goal: ドキュメントを使用して達成したい目標
            documents: 検索結果の一覧（JSON形式を想定）

        Returns:
            list[str]: 有用と判断されたドキュメントのリスト
        """
        prompt = PromptTemplate.from_template(GRADE_PROMPT)
        wrapper = LLMWrapper()
        chain = prompt | wrapper.get_structured_llm(
            RelevantDocuments, llm_instance=self._llm
        )

        result = await chain.ainvoke(
            {"goal": goal, "documents": documents}, self._config
        )

        return result

    # Edge Functions
    @log_function_start_end
    async def _should_continue(
        self, state: ResearcherState, config: RunnableConfig
    ) -> str:
        """ツールを呼び出すか終了するかを分岐させるエッジ"""
        last_message = state.messages[-1]

        # ツールの呼び出しがなければ終了する
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return END
        else:
            # ツールの実行可能回数が残っていればツールを実行
            if state.remaining_tool_call > 0:
                return "research"
            else:
                return END

    @log_function_start_end
    async def arun(self, research_goal: str) -> ResearcherState:
        """ワークフローを呼び出して、エージェントの最終回答を獲得する"""
        result = await self._workflow.ainvoke(
            {"goal": research_goal}, config=self._config
        )
        return ResearcherState(**result)


@tool(parse_docstring=True, response_format="content_and_artifact")
async def research_agent(
    goal: str,
    documents: Annotated[list[DocumentBase], InjectedToolArg],
    config: RunnableConfig,
) -> tuple[str, ResearcherState]:
    """Researcherエージェントに調査を依頼する

    Args:
        goal: エージェントが達成すべき明確なゴール
        documents: アクセス可能なドキュメント群

    Returns:
        str: Reseacherエージェントの回答
    """
    wrapper = LLMWrapper()
    llm = wrapper.get_llm(model_type=os.getenv("LLM_TYPE"), temperature=0)

    researcher = Researcher(llm, documents, config)
    result = await researcher.arun(goal)
    return result.messages[-1].content, result
