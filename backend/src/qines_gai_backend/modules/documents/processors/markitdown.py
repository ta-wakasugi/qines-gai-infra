"""MarkItDownプロセッサ"""

from langchain.docstore.document import Document
from markitdown import MarkItDown


class MarkItDownProcessor:
    """MarkItDownを使用して様々なファイル形式を処理するプロセッサ

    Word, Excel, PowerPoint, 画像など、PDFPlumberで対応していない
    ファイル形式をMarkItDownでMarkdownに変換して処理する。
    """

    def process(self, file_path: str) -> list[Document]:
        """ファイルを処理してDocumentリストを返す

        Args:
            file_path: 処理対象のファイルパス

        Returns:
            ファイル全体のテキストを含む1つのDocumentのリスト。
            metadataにはpage_num=1, total_pages=1が含まれる。

        Note:
            MarkItDownはページの概念がないため、常に1ページとして扱う。
        """
        markitdown = MarkItDown()
        result = markitdown.convert(file_path)
        parsed_content = result.text_content

        document = Document(
            page_content=parsed_content,
            metadata={
                "page_num": 1,
                "total_pages": 1,
            },
        )

        return [document]
