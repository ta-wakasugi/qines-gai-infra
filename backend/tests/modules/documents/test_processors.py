"""ドキュメントプロセッサのテストモジュール"""

from unittest.mock import MagicMock, patch

import pytest
from langchain.docstore.document import Document

from qines_gai_backend.modules.documents.processors.factory import get_processor
from qines_gai_backend.modules.documents.processors.markitdown import (
    MarkItDownProcessor,
)
from qines_gai_backend.modules.documents.processors.pdf import PDFProcessor


class TestGetProcessor:
    """get_processor関数のテストクラス"""

    @pytest.mark.parametrize(
        "extension,expected_type",
        [
            (".pdf", PDFProcessor),
            (".PDF", PDFProcessor),  # 大文字正規化
            (".docx", MarkItDownProcessor),  # デフォルトパスの代表例
            (".xyz", MarkItDownProcessor),  # 未知拡張子のフォールバック
        ],
    )
    def test_get_processor(self, extension, expected_type):
        """ファイル拡張子に応じて適切なプロセッサを返すことを検証"""
        processor = get_processor(extension)
        assert isinstance(processor, expected_type)


class TestPDFProcessor:
    """PDFProcessorのテストクラス"""

    def test_process_pdf_success(self):
        """PDFファイルのメタデータ変換が正しく行われることを検証"""
        processor = PDFProcessor()

        # モックのDocumentを作成
        mock_doc1 = Document(page_content="content1", metadata={"page": 0})
        mock_doc2 = Document(page_content="content2", metadata={"page": 1})
        mock_documents = [mock_doc1, mock_doc2]

        with patch(
            "qines_gai_backend.modules.documents.processors.pdf.PDFPlumberLoader"
        ) as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_documents
            mock_loader_class.return_value = mock_loader

            # Act
            result = processor.process("/test/path/test.pdf")

            # Assert - メタデータの変換ロジックを検証
            assert len(result) == 2
            assert result[0].metadata["page_num"] == 1
            assert result[0].metadata["total_pages"] == 2
            assert result[1].metadata["page_num"] == 2
            assert result[1].metadata["total_pages"] == 2

    def test_process_pdf_single_page(self):
        """1ページのPDFファイルのメタデータ変換を検証"""
        processor = PDFProcessor()

        mock_doc = Document(page_content="content", metadata={"page": 0})

        with patch(
            "qines_gai_backend.modules.documents.processors.pdf.PDFPlumberLoader"
        ) as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = [mock_doc]
            mock_loader_class.return_value = mock_loader

            # Act
            result = processor.process("/test/single.pdf")

            # Assert - メタデータの変換ロジックを検証
            assert len(result) == 1
            assert result[0].metadata["page_num"] == 1
            assert result[0].metadata["total_pages"] == 1


class TestMarkItDownProcessor:
    """MarkItDownProcessorのテストクラス"""

    def test_process_markitdown_success(self):
        """MarkItDownによるDocument生成とメタデータ設定を検証"""
        processor = MarkItDownProcessor()

        # モックの変換結果を作成
        mock_result = MagicMock()
        mock_result.text_content = "converted content"

        with patch(
            "qines_gai_backend.modules.documents.processors.markitdown.MarkItDown"
        ) as mock_markitdown_class:
            mock_markitdown = MagicMock()
            mock_markitdown.convert.return_value = mock_result
            mock_markitdown_class.return_value = mock_markitdown

            # Act
            result = processor.process("/test/path/test.docx")

            # Assert - Document生成とメタデータを検証
            assert len(result) == 1
            assert result[0].metadata["page_num"] == 1
            assert result[0].metadata["total_pages"] == 1

    def test_process_markitdown_empty_content(self):
        """空のコンテンツの処理を検証"""
        processor = MarkItDownProcessor()

        mock_result = MagicMock()
        mock_result.text_content = ""

        with patch(
            "qines_gai_backend.modules.documents.processors.markitdown.MarkItDown"
        ) as mock_markitdown_class:
            mock_markitdown = MagicMock()
            mock_markitdown.convert.return_value = mock_result
            mock_markitdown_class.return_value = mock_markitdown

            # Act
            result = processor.process("/test/empty.xlsx")

            # Assert - 空コンテンツでもDocument生成されることを検証
            assert len(result) == 1
            assert result[0].metadata["page_num"] == 1
            assert result[0].metadata["total_pages"] == 1
