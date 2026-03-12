"""ドキュメントプロセッサの基底クラスとプロトコル定義"""

from typing import Protocol

from langchain.docstore.document import Document


class DocumentProcessor(Protocol):
    """ドキュメントプロセッサのインターフェース

    ファイルを読み込み、LangChainのDocumentリストに変換する責務を持つ。
    各Documentのmetadataにはpage_num, total_pagesなどのメタデータを含む。

    Note:
        ページ番号は1始まりで統一する。ライブラリが0始まりの場合はプロセッサ内で+1する。
    """

    def process(self, file_path: str) -> list[Document]:
        """ファイルを処理してLangChainのDocumentリストを返す

        Args:
            file_path: 処理対象のファイルパス

        Returns:
            LangChainのDocumentのリスト。各Documentは以下のmetadataを持つ：
            - page_num (int): ページ番号（1始まり）
            - total_pages (int): 総ページ数

        Raises:
            Exception: ファイルの読み込みやパースに失敗した場合
        """
        ...
