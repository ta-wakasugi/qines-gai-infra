"""
LLMWrapper のユニットテスト

環境変数に依存するため、各テストでモックを使用
"""

import os
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from pydantic import BaseModel

from qines_gai_backend.modules.ai.llm_wrapper.wrapper import LLMWrapper


class OutputSchema(BaseModel):
    """テスト用の出力スキーマ"""

    result: str
    count: Optional[int] = None


class TestLLMWrapperInit:
    """LLMWrapper.__init__ のテストクラス"""

    @patch("qines_gai_backend.modules.ai.llm_wrapper.wrapper.load_dotenv")
    def test_init_success(self, mock_load_dotenv):
        """正常系：LLMWrapperの初期化が成功すること"""
        # Act
        wrapper = LLMWrapper()

        # Assert
        assert wrapper is not None
        mock_load_dotenv.assert_called_once_with("/app/.env")


class TestGetLLM:
    """LLMWrapper.get_llm のテストクラス"""

    @patch("qines_gai_backend.modules.ai.llm_wrapper.wrapper.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "LOCAL_MODEL": "test-model",
            "OPENAI_API_BASE": "http://localhost:8000",
        },
    )
    def test_get_llm_vllm(self, mock_load_dotenv):
        """正常系：vLLMのLLMインスタンスを取得できること"""
        # Arrange
        wrapper = LLMWrapper()

        # Act
        llm = wrapper.get_llm(model_type="vllm")

        # Assert
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "test-model"
        # SecretStrなので get_secret_value() で値を取得
        assert llm.openai_api_key.get_secret_value() == "EMPTY"
        assert llm.openai_api_base == "http://localhost:8000"
        assert llm.max_tokens == 25000
        assert llm.temperature == 0
        assert llm.streaming is True

    @patch("qines_gai_backend.modules.ai.llm_wrapper.wrapper.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_API_VERSION": "2024-02-01",
        },
    )
    def test_get_llm_azure(self, mock_load_dotenv):
        """正常系：Azure OpenAIのLLMインスタンスを取得できること"""
        # Arrange
        wrapper = LLMWrapper()

        # Act
        llm = wrapper.get_llm(model_type="azure")

        # Assert
        assert isinstance(llm, AzureChatOpenAI)
        assert llm.deployment_name == "gpt-4o"
        assert llm.temperature == 0

    @patch("qines_gai_backend.modules.ai.llm_wrapper.wrapper.load_dotenv")
    def test_get_llm_no_type(self, mock_load_dotenv):
        """異常系：モデルタイプが指定されていない場合、ValueErrorが発生すること"""
        # Arrange
        wrapper = LLMWrapper()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            wrapper.get_llm()

        assert "No model type specified" in str(exc_info.value)

    @patch("qines_gai_backend.modules.ai.llm_wrapper.wrapper.load_dotenv")
    @patch.dict(os.environ, {}, clear=True)
    def test_get_llm_azure_missing_env(self, mock_load_dotenv):
        """異常系：Azure環境変数が不足している場合、ValueErrorが発生すること"""
        # Arrange
        wrapper = LLMWrapper()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            wrapper.get_llm(model_type="azure")

        assert "Azure OpenAI environment variables are not completely set" in str(
            exc_info.value
        )

    @patch("qines_gai_backend.modules.ai.llm_wrapper.wrapper.load_dotenv")
    def test_get_llm_unsupported_type(self, mock_load_dotenv):
        """異常系：サポートされていないモデルタイプの場合、ValueErrorが発生すること"""
        # Arrange
        wrapper = LLMWrapper()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            wrapper.get_llm(model_type="unsupported")

        assert "Unsupported model type: unsupported" in str(exc_info.value)

    @patch("qines_gai_backend.modules.ai.llm_wrapper.wrapper.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_API_VERSION": "2024-02-01",
        },
    )
    def test_get_llm_with_temperature(self, mock_load_dotenv):
        """正常系：temperatureパラメータが正しく設定されること"""
        # Arrange
        wrapper = LLMWrapper()

        # Act
        llm = wrapper.get_llm(model_type="azure", temperature=0.7)

        # Assert
        assert isinstance(llm, AzureChatOpenAI)
        assert llm.temperature == 0.7


class TestGetStructuredLLM:
    """LLMWrapper.get_structured_llm のテストクラス"""

    @patch("qines_gai_backend.modules.ai.llm_wrapper.wrapper.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "LLM_TYPE": "vllm",
            "LOCAL_MODEL": "test-model",
            "OPENAI_API_BASE": "http://localhost:8000",
        },
    )
    def test_get_structured_llm_vllm(self, mock_load_dotenv):
        """正常系：vLLMの構造化出力対応LLMを取得できること（json_schema）"""
        # Arrange
        wrapper = LLMWrapper()

        # Act
        structured_llm = wrapper.get_structured_llm(OutputSchema)

        # Assert
        assert structured_llm is not None
        # with_structured_outputが呼ばれていることを確認（詳細は内部実装依存）

    @patch("qines_gai_backend.modules.ai.llm_wrapper.wrapper.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "LLM_TYPE": "azure",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_API_VERSION": "2024-02-01",
        },
    )
    def test_get_structured_llm_azure(self, mock_load_dotenv):
        """正常系：Azureの構造化出力対応LLMを取得できること（function_calling）"""
        # Arrange
        wrapper = LLMWrapper()

        # Act
        structured_llm = wrapper.get_structured_llm(OutputSchema)

        # Assert
        assert structured_llm is not None

    @patch("qines_gai_backend.modules.ai.llm_wrapper.wrapper.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "LLM_TYPE": "azure",
        },
    )
    def test_get_structured_llm_with_llm_instance(self, mock_load_dotenv):
        """正常系：既存のLLMインスタンスを渡した場合、それを使用すること"""
        # Arrange
        wrapper = LLMWrapper()

        # 既存のLLMインスタンスをモック
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        # Act
        structured_llm = wrapper.get_structured_llm(OutputSchema, llm_instance=mock_llm)

        # Assert
        assert structured_llm == mock_structured_llm
        mock_llm.with_structured_output.assert_called_once_with(
            OutputSchema, method="function_calling"
        )

    @patch("qines_gai_backend.modules.ai.llm_wrapper.wrapper.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "LLM_TYPE": "unsupported",
        },
    )
    def test_get_structured_llm_unsupported_type(self, mock_load_dotenv):
        """異常系：サポートされていないモデルタイプの場合、ValueErrorが発生すること"""
        # Arrange
        wrapper = LLMWrapper()

        # 既存のLLMインスタンスをモック（get_llmをスキップするため）
        mock_llm = MagicMock()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            wrapper.get_structured_llm(OutputSchema, llm_instance=mock_llm)

        assert "Unsupported model type: unsupported" in str(exc_info.value)
