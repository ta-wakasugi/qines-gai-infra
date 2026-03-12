import os

from dotenv import load_dotenv
from langchain.llms.base import BaseLLM
from langchain_openai import AzureChatOpenAI, ChatOpenAI


class LLMWrapper:
    def __init__(self):
        # .env.backendを読み込み
        load_dotenv("/app/.env")

    def get_llm(self, model_type: str = None, temperature: float = 0) -> BaseLLM:
        """
        LLMインスタンスを取得
        Args:
            model_type (str, optional): LLMの種類 ex.)("ollama" or "azure")
            temperature (float, optional): temperatureの値
        Returns:
            BaseLLM: LLMインスタンス
        Raises:
            ValueError: モデルタイプが指定されていない、または環境変数に設定されていない場合
        """
        # # 引数またはデフォルトのモデルタイプを取得
        # model_type = model_type or os.getenv("LLM_TYPE")
        # モデルタイプが指定されていない場合はエラーを投げる
        if not model_type:
            raise ValueError(
                "No model type specified. Please provide a model type or set the LLM_TYPE environment variable."
            )

        # モデルタイプに基づいてLLMインスタンスを返す
        if model_type.lower() == "vllm":
            return ChatOpenAI(
                model=os.getenv("LOCAL_MODEL"),
                openai_api_key="EMPTY",
                openai_api_base=os.getenv("OPENAI_API_BASE"),
                max_tokens=25000,
                temperature=0,
                streaming=True,
            )
        elif model_type.lower() == "azure":
            # Azureの環境変数が設定されていない場合もエラーを投げる
            if not all(
                [
                    os.getenv("AZURE_OPENAI_ENDPOINT"),
                    os.getenv("AZURE_OPENAI_API_KEY"),
                ]
            ):
                raise ValueError(
                    "Azure OpenAI environment variables are not completely set."
                )

            return AzureChatOpenAI(
                azure_deployment="gpt-4o",
                temperature=temperature,
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            )
        else:
            # サポートされていないモデルタイプの場合
            raise ValueError(f"Unsupported model type: {model_type}")

    def get_structured_llm(
        self, output_schema, temperature: float = 0, llm_instance: BaseLLM = None
    ):
        """
        構造化出力対応のLLMを取得する

        Args:
            output_schema: 出力スキーマ
            temperature (float, optional): temperatureの値
            llm_instance (BaseLLM, optional): 既存のLLMインスタンス（Noneの場合は新規作成）

        Returns:
            構造化出力対応のLLMインスタンス

        Raises:
            ValueError: サポートされていないモデルタイプの場合
        """
        model_type = os.getenv("LLM_TYPE")

        # LLMインスタンスが渡されていない場合は新規作成
        if llm_instance is None:
            llm_instance = self.get_llm(model_type=model_type, temperature=temperature)

        # モデルタイプに基づいて適切なメソッドを選択
        if model_type.lower() == "vllm":
            return llm_instance.with_structured_output(
                output_schema, method="json_schema"
            )
        elif model_type.lower() == "azure":
            return llm_instance.with_structured_output(
                output_schema, method="function_calling"
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
