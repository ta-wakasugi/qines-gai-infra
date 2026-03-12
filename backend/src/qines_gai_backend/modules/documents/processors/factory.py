"""ドキュメントプロセッサのファクトリー"""

from qines_gai_backend.modules.documents.processors.base import DocumentProcessor
from qines_gai_backend.modules.documents.processors.markitdown import (
    MarkItDownProcessor,
)
from qines_gai_backend.modules.documents.processors.pdf import PDFProcessor
from qines_gai_backend.modules.documents.processors.excel import ExcelProcessor


def get_processor(file_extension: str) -> DocumentProcessor:
    """ファイル拡張子に応じた適切なプロセッサを返す

    Args:
        file_extension: ファイルの拡張子（例: ".pdf", ".docx"）

    Returns:
        適切なDocumentProcessor実装

    Note:
        - PDFファイルにはPDFProcessor（PDFPlumberLoader使用）
        - その他のファイルにはMarkItDownProcessor（汎用的に対応）
    """
    # 拡張子を小文字に正規化
    ext = file_extension.lower()

    # ファイルタイプごとのマッピング
    processor_mapping = {
        ".pdf": PDFProcessor(),
        ".xlsx": ExcelProcessor(),
        ".xlsm": ExcelProcessor(),
    }

    # マッピングに存在すればそれを返し、なければデフォルトのMarkItDown
    return processor_mapping.get(ext, MarkItDownProcessor())
