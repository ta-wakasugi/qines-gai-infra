"""PDFドキュメントプロセッサ"""

from langchain.docstore.document import Document
from langchain_community.document_loaders import PDFPlumberLoader


class PDFProcessor:
    """PDFファイルをページごとに処理するプロセッサ

    LangChainのPDFPlumberLoaderを使用してPDFを解析する。
    metadataを正規化し、ページ番号を1始まりに統一する。
    """

    def process(self, file_path: str) -> list[Document]:
        """PDFファイルを処理してページごとのDocumentリストを返す

        Args:
            file_path: PDFファイルのパス

        Returns:
            各ページのテキストを含むDocumentのリスト。
            metadataにはpage_num（1始まり）とtotal_pagesが含まれる。
        """
        loader = PDFPlumberLoader(file_path)
        documents = loader.load()

        # metadataを正規化
        total_pages = len(documents)
        for i, doc in enumerate(documents):
            # PDFPlumberLoaderのpage番号は0始まりなので1始まりに変換
            doc.metadata["page_num"] = i + 1
            doc.metadata["total_pages"] = total_pages

        return documents
