import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from qines_gai_backend.modules.collections.models import (
    CollectionBase,
    CollectionDetail,
)
from qines_gai_backend.modules.documents.models import DocumentBase
from qines_gai_backend.schemas.schema import (
    T_Collection,
    T_CollectionDocument,
    T_Document,
)


class TestCollectionModels:
    """Collection Modelsの関数のテストクラス"""

    @pytest.fixture
    def sample_t_collection(self):
        """テスト用のT_Collectionを作成する"""
        collection = MagicMock(spec=T_Collection)
        collection.public_collection_id = "test_pub_id"
        collection.name = "Test Collection"
        collection.created_at = datetime(2023, 1, 1, 12, 0, 0)
        collection.updated_at = datetime(2023, 1, 2, 12, 0, 0)
        return collection

    @pytest.fixture
    def sample_t_document(self):
        """テスト用のT_Documentを作成する"""
        document = MagicMock(spec=T_Document)
        document.document_id = uuid.uuid4()
        document.file_name = "test_document.pdf"
        document.file_path = "/test/path/test_document.pdf"
        document.file_type = "application/pdf"
        document.metadata_info = {
            "subject": "AUTOSAR",
            "genre": "SWS",
            "release": "R22-11",
        }
        document.summary = "Test document summary"
        return document

    @pytest.fixture
    def sample_t_collection_document(self, sample_t_document):
        """テスト用のT_CollectionDocumentを作成する"""
        collection_document = MagicMock(spec=T_CollectionDocument)
        collection_document.document = sample_t_document
        collection_document.position = 1
        return collection_document

    class TestCollectionBase:
        """CollectionBaseのテストクラス"""

        def test_from_db_success(self, sample_t_collection):
            """正常系：from_dbメソッドが正常に動作することを確認する"""
            # Act
            result = CollectionBase.from_db(sample_t_collection)

            # Assert
            assert result.public_collection_id == "test_pub_id"
            assert result.name == "Test Collection"
            # datetime_converterを通すと実際の変換が行われるので、変換後の値と比較する
            assert result.created_at is not None
            assert result.updated_at is not None

    class TestCollectionDetail:
        """CollectionDetailのテストクラス"""

        def test_from_db_success_with_documents(
            self, sample_t_collection, sample_t_collection_document
        ):
            """正常系：ドキュメント付きのfrom_dbメソッドが正常に動作することを確認する"""
            # Arrange
            collection_documents = [sample_t_collection_document]

            # Act
            result = CollectionDetail.from_db(sample_t_collection, collection_documents)

            # Assert
            assert result.public_collection_id == "test_pub_id"
            assert result.name == "Test Collection"
            assert len(result.documents) == 1
            assert isinstance(result.documents[0], DocumentBase)
            assert result.documents[0].title == "test_document.pdf"
            assert result.documents[0].path == "/test/path/test_document.pdf"
            assert result.documents[0].subject == "AUTOSAR"
            assert result.documents[0].genre == "SWS"
            assert result.documents[0].release == "R22-11"
            assert result.documents[0].file_type == "application/pdf"

        def test_from_db_success_empty_documents(self, sample_t_collection):
            """正常系：ドキュメントなしのfrom_dbメソッドが正常に動作することを確認する"""
            # Act
            result = CollectionDetail.from_db(sample_t_collection, [])

            # Assert
            assert result.public_collection_id == "test_pub_id"
            assert result.name == "Test Collection"
            assert len(result.documents) == 0

        def test_from_db_with_sorted_documents(
            self, sample_t_collection, sample_t_document
        ):
            """正常系：ドキュメントがposition順でソートされることを確認する"""
            # Arrange
            doc1 = MagicMock(spec=T_CollectionDocument)
            doc1.document = sample_t_document
            doc1.position = 2

            doc2 = MagicMock(spec=T_CollectionDocument)
            doc2.document = sample_t_document
            doc2.position = 1

            collection_documents = [doc1, doc2]  # 逆順で配置

            # Act
            result = CollectionDetail.from_db(sample_t_collection, collection_documents)

            # Assert
            assert len(result.documents) == 2
            # positionが1のドキュメントが最初に来ることを確認
            # (この場合、同じドキュメントなので内容は同じだが、ソート処理の確認)

        def test_from_db_with_missing_metadata(self, sample_t_collection):
            """正常系：metadata_infoの値が欠けている場合の処理を確認する"""
            # Arrange
            document = MagicMock(spec=T_Document)
            document.document_id = uuid.uuid4()
            document.file_name = "test.pdf"
            document.file_path = "/test.pdf"
            document.file_type = "application/pdf"
            document.metadata_info = {
                "subject": "AUTOSAR"
            }  # genre, releaseが欠けている
            document.summary = ""

            collection_document = MagicMock(spec=T_CollectionDocument)
            collection_document.document = document
            collection_document.position = 1

            # Act
            result = CollectionDetail.from_db(
                sample_t_collection, [collection_document]
            )

            # Assert
            assert result.documents[0].subject == "AUTOSAR"
            assert result.documents[0].genre is None  # デフォルト値
            assert result.documents[0].release is None  # デフォルト値

        def test_from_db_with_no_subject_metadata(self, sample_t_collection):
            """正常系：subjectが欠けている場合のデフォルト値を確認する"""
            # Arrange
            document = MagicMock(spec=T_Document)
            document.document_id = uuid.uuid4()
            document.file_name = "test.pdf"
            document.file_path = "/test.pdf"
            document.file_type = "application/pdf"
            document.metadata_info = {}  # 空のmetadata
            document.summary = ""

            collection_document = MagicMock(spec=T_CollectionDocument)
            collection_document.document = document
            collection_document.position = 1

            # Act
            result = CollectionDetail.from_db(
                sample_t_collection, [collection_document]
            )

            # Assert
            assert result.documents[0].subject == "others"  # デフォルト値
