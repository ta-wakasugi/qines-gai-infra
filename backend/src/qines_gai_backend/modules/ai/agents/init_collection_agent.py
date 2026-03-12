import json
import os
from typing import Annotated, List, Literal, Sequence, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from meilisearch_python_sdk import AsyncClient

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.ai.llm_wrapper import LLMWrapper

load_dotenv("/app/.env")
logger = get_logger(__name__)


class InitCollectionAgentState(TypedDict):
    """
    InitCollectionAgentの状態を保持するためのTypedDict。
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]
    retrieval_attempts: int
    question_list: List[str]
    document_ids: List[str]


class InitCollectionAgent:
    """
    ユーザからの質問に基づいて初期コレクションを生成するためのエージェント。
    """

    @log_function_start_end
    async def collection(self, meili_client: AsyncClient, user_question: str) -> str:
        """
        キーワードの抽出、ドキュメントの検索、およびコレクション名生成を行う。

        Args:
            meili_client (AsyncClient): Meilisearchとのやり取りを行うクライアント。
            user_question (str): 関連するドキュメントを収集するためのユーザの質問。

        Returns:
            str: コレクション名と関連ドキュメントIDが含まれたJSONエンコードされた文字列。
        """

        @log_function_start_end
        def extract_keywords(query: str) -> str:
            """
            提供されたユーザの質問から検索キーワードに変換する。
            """
            wrapper = LLMWrapper()
            model = wrapper.get_llm(model_type=os.getenv("LLM_TYPE"), temperature=0)
            prompt = PromptTemplate(
                template="""Extract the main keywords from the following user question and return them as a comma-separated list, without additional commentary:
        
                        User question: {question}
                        Keywords:""",
                input_variables=["question"],
            )
            chain = prompt | model | StrOutputParser()
            result = chain.invoke({"question": query})
            keywords = result.strip()
            return keywords

        @log_function_start_end
        def generate_collection_name(query: str) -> str:
            """
            ユーザリクエストに基づいてドキュメント群の名前をLLMで生成する。
            """
            wrapper = LLMWrapper()
            model = wrapper.get_llm(model_type=os.getenv("LLM_TYPE"), temperature=0)
            prompt = PromptTemplate(
                template="""Given the user's request below, propose a short, descriptive name for the collection of documents that address this request. Keep it concise and meaningful.
        
                        User request: {question}
                        Name:""",
                input_variables=["question"],
            )
            chain = prompt | model | StrOutputParser()
            result = chain.invoke({"question": query})
            doc_name = result.strip()
            return doc_name

        @log_function_start_end
        async def meilisearch_retrieve(state):
            """
            ユーザの質問から抽出したキーワードを使用して、ドキュメントの検索を行う。
            """
            messages = state["messages"]
            question = messages[-1].content

            keywords = extract_keywords(question)

            index = meili_client.index("qines-gai")
            results = await index.search(keywords)
            hits = results.hits
            doc_ids = [hit.get("doc_id") for hit in hits]

            state["retrieval_attempts"] += 1

            # 既にdocument_idsに登録されているIDは抜いて追加する
            unique_doc_ids = set(doc_ids) - set(state["document_ids"])
            state["document_ids"].extend(unique_doc_ids)

            result_json = {"document_ids": doc_ids}
            return {
                "messages": [
                    HumanMessage(content=json.dumps(result_json, ensure_ascii=False))
                ],
                "retrieval_attempts": state["retrieval_attempts"],
                "document_ids": state["document_ids"],
            }

        @log_function_start_end
        def should_retrieve(state) -> Literal["generate", "rewrite"]:
            """
            追加再取得を行う必要があるか、または最終レスポンスを生成するかを判断する。
            """
            doc_ids = state["document_ids"]

            retrieval_attempts = state.get("retrieval_attempts", 0)

            if len(doc_ids) < 5 and retrieval_attempts < 3:
                logger.info("---DECISION: NEED MORE DOCS---")
                return "rewrite"
            else:
                logger.info("---DECISION: SUFFICIENT DOCS---")
                return "generate"

        @log_function_start_end
        def rewrite(state):
            """
            初期および以前に検索された質問に基づいて質問を変換する。
            """
            messages = state["messages"]
            question = messages[0].content
            state["question_list"].append(question)
            question_list = state["question_list"]
            msg = [
                HumanMessage(
                    content=f""" 
                        Look at the input and try to reason about the underlying semantic intent / meaning. 
                        Consider translating the question into English if it is not in English.
                        However, please avoid questions that are the same as the searched question.
                        Here is the initial question:
                        -------
                        {question} 
                        -------
                        Here is the searched questions: 
                        -------
                        {question_list}
                        -------
                        Formulate an improved question:""",
                )
            ]

            wrapper = LLMWrapper()
            model = wrapper.get_llm(model_type=os.getenv("LLM_TYPE"), temperature=0)

            response = model.invoke(msg)
            state["question_list"].append(response.content)
            return {"messages": [response], "question_list": state["question_list"]}

        @log_function_start_end
        def generate(state):
            """
            最終的な出力として、ドキュメントIDのリストとコレクション名を返す。
            """
            messages = state["messages"]
            # 最初のユーザ質問を取得
            question = messages[0].content

            docs = state["document_ids"]

            doc_name = generate_collection_name(question)

            response_json = {"name": doc_name, "document_ids": docs}

            return {
                "messages": [
                    HumanMessage(content=json.dumps(response_json, ensure_ascii=False))
                ]
            }

        workflow = StateGraph(InitCollectionAgentState)
        workflow.add_node("meilisearch_retrieve", meilisearch_retrieve)
        workflow.add_node("rewrite", rewrite)
        workflow.add_node("generate", generate)

        workflow.add_edge(START, "meilisearch_retrieve")
        workflow.add_conditional_edges("meilisearch_retrieve", should_retrieve)
        workflow.add_edge("generate", END)
        workflow.add_edge("rewrite", "meilisearch_retrieve")

        app = workflow.compile()

        inputs = {
            "messages": [
                ("user", user_question),
            ],
            "retrieval_attempts": 0,
            "document_ids": [],
            "question_list": [],
        }

        async for output in app.astream(inputs):
            if "generate" in output:
                last_message = output["generate"]["messages"][-1]
                doc_json = json.loads(last_message.content)

        return json.dumps(doc_json, ensure_ascii=False)
