"""
convert_md_to_pptx モジュールのユニットテスト
"""

from unittest.mock import MagicMock, patch

import pytest

from qines_gai_backend.modules.ai.convert_md_to_pptx import markdown_to_powerpoint
from qines_gai_backend.modules.artifacts.models import (
    PowerPoint,
    TextPage,
    TextSection,
)


class TestMarkdownToPowerpoint:
    """markdown_to_powerpoint のテストクラス"""

    @patch("qines_gai_backend.modules.ai.convert_md_to_pptx.LLMWrapper")
    def test_markdown_to_powerpoint_success(self, mock_wrapper_class):
        """正常系：MarkdownをPowerPointオブジェクトに変換できること"""
        # Arrange
        markdown_input = "# テストタイトル\n\n## セクション1\n\nテスト内容"

        # 期待されるPowerPointオブジェクトを作成
        expected_powerpoint = PowerPoint(
            title="テストプレゼンテーション",
            pages=[
                TextPage(
                    header="テストタイトル",
                    content="テスト内容",
                    template="text",
                    policy="テストポリシー",
                    sections=[
                        TextSection(
                            title="セクション1",
                            content=["テスト内容"],
                        )
                    ],
                )
            ],
        )

        # LLMWrapperとstructured_llmをモック
        mock_wrapper = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = expected_powerpoint
        mock_wrapper.get_structured_llm.return_value = mock_structured_llm
        mock_wrapper_class.return_value = mock_wrapper

        # Act
        result = markdown_to_powerpoint(markdown_input)

        # Assert
        assert isinstance(result, PowerPoint)
        assert result.title == "テストプレゼンテーション"
        assert len(result.pages) == 1
        assert result.pages[0].header == "テストタイトル"

        # LLMWrapperの呼び出しを確認
        mock_wrapper_class.assert_called_once()
        mock_wrapper.get_structured_llm.assert_called_once_with(
            PowerPoint, temperature=0
        )
        mock_structured_llm.invoke.assert_called_once()

        # プロンプトにmarkdown_inputが含まれていることを確認
        call_args = mock_structured_llm.invoke.call_args
        prompt = call_args[0][0]
        assert markdown_input in prompt
        assert "PowerPointオブジェクト作成" in prompt

    @patch("qines_gai_backend.modules.ai.convert_md_to_pptx.LLMWrapper")
    def test_markdown_to_powerpoint_with_empty_input(self, mock_wrapper_class):
        """正常系：空のMarkdownでも変換できること"""
        # Arrange
        markdown_input = ""

        expected_powerpoint = PowerPoint(
            title="空のプレゼンテーション",
            pages=[],
        )

        mock_wrapper = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = expected_powerpoint
        mock_wrapper.get_structured_llm.return_value = mock_structured_llm
        mock_wrapper_class.return_value = mock_wrapper

        # Act
        result = markdown_to_powerpoint(markdown_input)

        # Assert
        assert isinstance(result, PowerPoint)
        assert result.title == "空のプレゼンテーション"
        assert len(result.pages) == 0

    @patch("qines_gai_backend.modules.ai.convert_md_to_pptx.LLMWrapper")
    def test_markdown_to_powerpoint_with_complex_markdown(self, mock_wrapper_class):
        """正常系：複雑なMarkdownも変換できること"""
        # Arrange
        markdown_input = """# メインタイトル

## セクション1
テキスト1

## セクション2
テキスト2

| 列1 | 列2 |
|-----|-----|
| A   | B   |
"""

        expected_powerpoint = PowerPoint(
            title="複雑なプレゼンテーション",
            pages=[
                TextPage(
                    header="セクション1",
                    content="テキスト1",
                    template="text",
                    policy="テストポリシー",
                    sections=[TextSection(title="セクション1", content=["テキスト1"])],
                ),
                TextPage(
                    header="セクション2",
                    content="テキスト2",
                    template="text",
                    policy="テストポリシー",
                    sections=[TextSection(title="セクション2", content=["テキスト2"])],
                ),
            ],
        )

        mock_wrapper = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = expected_powerpoint
        mock_wrapper.get_structured_llm.return_value = mock_structured_llm
        mock_wrapper_class.return_value = mock_wrapper

        # Act
        result = markdown_to_powerpoint(markdown_input)

        # Assert
        assert isinstance(result, PowerPoint)
        assert result.title == "複雑なプレゼンテーション"
        assert len(result.pages) == 2

    @patch("qines_gai_backend.modules.ai.convert_md_to_pptx.LLMWrapper")
    def test_markdown_to_powerpoint_llm_error(self, mock_wrapper_class):
        """異常系：LLMがエラーを返した場合、例外が発生すること"""
        # Arrange
        markdown_input = "# テスト"

        mock_wrapper = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.side_effect = Exception("LLM error")
        mock_wrapper.get_structured_llm.return_value = mock_structured_llm
        mock_wrapper_class.return_value = mock_wrapper

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            markdown_to_powerpoint(markdown_input)

        assert "LLM error" in str(exc_info.value)
