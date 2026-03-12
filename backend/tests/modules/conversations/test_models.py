import uuid
from unittest.mock import MagicMock

import pytest

from qines_gai_backend.modules.conversations.models import (
    Artifact,
    MessageMetadata,
)
from qines_gai_backend.schemas.schema import T_Artifact, T_Message


class TestMessageMetadataFromDb:
    """MessageMetadata.from_dbメソッドのテストクラス"""

    @pytest.fixture
    def mock_message(self):
        """T_Messageのモックを作成する"""
        return MagicMock(spec=T_Message)

    def test_from_db_with_all_fields(self, mock_message):
        """全てのフィールドが設定されている場合の正常系テスト"""
        # Arrange
        mock_message.metadata_info = {
            "version": "v2",
            "contexts": [
                {
                    "title": "Test Document",
                    "chunk": "Test chunk content",
                    "path": "/test/path/document.pdf",
                    "page": 5,
                    "file_type": "application/pdf",
                }
            ],
            "recommended_documents": [
                {
                    "id": "test-doc-id",
                    "title": "Test Document",
                    "path": "/test/path/document.pdf",
                    "subject": "AUTOSAR",
                    "genre": "Test Genre",
                    "release": "R22-11",
                    "file_type": "application/pdf",
                }
            ],
            "generated_artifacts": [{"id": "test-artifact-id", "version": 1}],
        }

        # Act
        result = MessageMetadata.from_db(mock_message)

        # Assert
        assert result.version == "v2"
        assert len(result.contexts) == 1
        assert result.contexts[0].title == "Test Document"
        assert result.contexts[0].chunk == "Test chunk content"
        assert result.contexts[0].path == "/test/path/document.pdf"
        assert result.contexts[0].page == 5

        assert len(result.recommended_documents) == 1
        assert result.recommended_documents[0].id == "test-doc-id"
        assert result.recommended_documents[0].title == "Test Document"
        assert result.recommended_documents[0].genre == "Test Genre"
        assert result.recommended_documents[0].release == "R22-11"

        assert len(result.generated_artifacts) == 1
        assert result.generated_artifacts[0].id == "test-artifact-id"
        assert result.generated_artifacts[0].version == 1

    def test_from_db_with_minimal_fields(self, mock_message):
        """最小限のフィールドのみ設定されている場合のテスト"""
        # Arrange
        mock_message.metadata_info = {}

        # Act
        result = MessageMetadata.from_db(mock_message)

        # Assert
        assert result.version == "v1"  # デフォルト値
        assert result.contexts is None
        assert result.recommended_documents is None
        assert result.generated_artifacts is None

    def test_from_db_with_empty_version(self, mock_message):
        """versionが空の場合のテスト"""
        # Arrange
        mock_message.metadata_info = {"version": ""}

        # Act
        result = MessageMetadata.from_db(mock_message)

        # Assert
        assert result.version == "v1"  # デフォルト値

    def test_from_db_with_version_none(self, mock_message):
        """versionがNoneの場合のテスト"""
        # Arrange
        mock_message.metadata_info = {"version": None}

        # Act
        result = MessageMetadata.from_db(mock_message)

        # Assert
        assert result.version == "v1"  # デフォルト値

    def test_from_db_with_empty_contexts(self, mock_message):
        """contextsが空リストの場合のテスト"""
        # Arrange
        mock_message.metadata_info = {"contexts": []}

        # Act
        result = MessageMetadata.from_db(mock_message)

        # Assert
        assert result.contexts is None

    def test_from_db_with_multiple_contexts(self, mock_message):
        """複数のcontextsがある場合のテスト"""
        # Arrange
        mock_message.metadata_info = {
            "contexts": [
                {
                    "title": "Document 1",
                    "chunk": "Chunk 1",
                    "path": "/path/doc1.pdf",
                    "page": 1,
                    "file_type": "application/pdf",
                },
                {
                    "title": "Document 2",
                    "chunk": "Chunk 2",
                    "path": "/path/doc2.pdf",
                    "page": 2,
                    "file_type": "application/pdf",
                },
            ]
        }

        # Act
        result = MessageMetadata.from_db(mock_message)

        # Assert
        assert len(result.contexts) == 2
        assert result.contexts[0].title == "Document 1"
        assert result.contexts[1].title == "Document 2"

    def test_from_db_with_empty_recommended_documents(self, mock_message):
        """recommended_documentsが空リストの場合のテスト"""
        # Arrange
        mock_message.metadata_info = {"recommended_documents": []}

        # Act
        result = MessageMetadata.from_db(mock_message)

        # Assert
        assert result.recommended_documents is None

    def test_from_db_with_document_missing_optional_fields(self, mock_message):
        """ドキュメントでオプションフィールドが欠けている場合のテスト"""
        # Arrange
        mock_message.metadata_info = {
            "recommended_documents": [
                {
                    "id": "test-doc-id",
                    "title": "Test Document",
                    "path": "/test/path/document.pdf",
                    "subject": "others",
                    # genre と release が欠けている
                    "file_type": "application/pdf",
                }
            ]
        }

        # Act
        result = MessageMetadata.from_db(mock_message)

        # Assert
        assert len(result.recommended_documents) == 1
        assert result.recommended_documents[0].genre is None
        assert result.recommended_documents[0].release is None

    def test_from_db_with_empty_generated_artifacts(self, mock_message):
        """generated_artifactsが空リストの場合のテスト"""
        # Arrange
        mock_message.metadata_info = {"generated_artifacts": []}

        # Act
        result = MessageMetadata.from_db(mock_message)

        # Assert
        assert result.generated_artifacts is None

    def test_from_db_with_multiple_generated_artifacts(self, mock_message):
        """複数のgenerated_artifactsがある場合のテスト"""
        # Arrange
        mock_message.metadata_info = {
            "generated_artifacts": [
                {"id": "artifact-1", "version": 1},
                {"id": "artifact-2", "version": 2},
            ]
        }

        # Act
        result = MessageMetadata.from_db(mock_message)

        # Assert
        assert len(result.generated_artifacts) == 2
        assert result.generated_artifacts[0].id == "artifact-1"
        assert result.generated_artifacts[0].version == 1
        assert result.generated_artifacts[1].id == "artifact-2"
        assert result.generated_artifacts[1].version == 2

    def test_from_db_with_none_values_in_metadata(self, mock_message):
        """メタデータのフィールドがNoneの場合のテスト"""
        # Arrange
        mock_message.metadata_info = {
            "contexts": None,
            "recommended_documents": None,
            "generated_artifacts": None,
        }

        # Act
        result = MessageMetadata.from_db(mock_message)

        # Assert
        assert result.contexts is None
        assert result.recommended_documents is None
        assert result.generated_artifacts is None

    def test_from_db_with_complex_metadata_combinations(self, mock_message):
        """複雑なメタデータの組み合わせのテスト"""
        # Arrange
        mock_message.metadata_info = {
            "version": "v3",
            "contexts": [
                {
                    "title": "Complex Document",
                    "chunk": "Complex chunk with special characters: 日本語テスト",
                    "path": "/complex/path/with spaces/document.pdf",
                    "page": 100,
                    "file_type": "application/pdf",
                }
            ],
            "recommended_documents": [
                {
                    "id": "complex-doc-id",
                    "title": "Complex Document Title",
                    "path": "/complex/path/document.pdf",
                    "subject": "AUTOSAR",
                    "genre": None,  # 明示的にNone
                    "release": "R23-11",
                    "file_type": "application/pdf",
                }
            ],
            "generated_artifacts": [],  # 空リスト
        }

        # Act
        result = MessageMetadata.from_db(mock_message)

        # Assert
        assert result.version == "v3"
        assert len(result.contexts) == 1
        assert "日本語テスト" in result.contexts[0].chunk
        assert len(result.recommended_documents) == 1
        assert result.recommended_documents[0].genre is None
        assert result.generated_artifacts is None  # 空リストはNoneになる


class TestArtifactFromDb:
    """Artifact.from_dbメソッドのテストクラス"""

    @pytest.fixture
    def mock_artifact(self):
        """T_Artifactのモックを作成する"""
        return MagicMock(spec=T_Artifact)

    def test_from_db_success(self, mock_artifact):
        """正常系テスト"""
        # Arrange
        artifact_id = uuid.uuid4()
        mock_artifact.artifact_id = artifact_id
        mock_artifact.version = 1
        mock_artifact.title = "Test Artifact Title"
        mock_artifact.content = "Test artifact content"

        # Act
        result = Artifact.from_db(mock_artifact)

        # Assert
        assert result.id == str(artifact_id)
        assert result.version == 1
        assert result.title == "Test Artifact Title"
        assert result.content == "Test artifact content"

    def test_from_db_with_unicode_content(self, mock_artifact):
        """Unicode文字を含むコンテンツのテスト"""
        # Arrange
        artifact_id = uuid.uuid4()
        mock_artifact.artifact_id = artifact_id
        mock_artifact.version = 2
        mock_artifact.title = "日本語タイトル"
        mock_artifact.content = "これは日本語のコンテンツです。特殊文字: ①②③"

        # Act
        result = Artifact.from_db(mock_artifact)

        # Assert
        assert result.id == str(artifact_id)
        assert result.version == 2
        assert result.title == "日本語タイトル"
        assert result.content == "これは日本語のコンテンツです。特殊文字: ①②③"

    def test_from_db_with_long_content(self, mock_artifact):
        """長いコンテンツのテスト"""
        # Arrange
        artifact_id = uuid.uuid4()
        mock_artifact.artifact_id = artifact_id
        mock_artifact.version = 5
        mock_artifact.title = "Long Content Test"
        mock_artifact.content = "A" * 10000  # 10000文字の長い文字列

        # Act
        result = Artifact.from_db(mock_artifact)

        # Assert
        assert result.id == str(artifact_id)
        assert result.version == 5
        assert result.title == "Long Content Test"
        assert len(result.content) == 10000
        assert result.content == "A" * 10000

    def test_from_db_with_empty_content(self, mock_artifact):
        """空のコンテンツのテスト"""
        # Arrange
        artifact_id = uuid.uuid4()
        mock_artifact.artifact_id = artifact_id
        mock_artifact.version = 0
        mock_artifact.title = ""
        mock_artifact.content = ""

        # Act
        result = Artifact.from_db(mock_artifact)

        # Assert
        assert result.id == str(artifact_id)
        assert result.version == 0
        assert result.title == ""
        assert result.content == ""

    def test_from_db_with_high_version_number(self, mock_artifact):
        """高いバージョン番号のテスト"""
        # Arrange
        artifact_id = uuid.uuid4()
        mock_artifact.artifact_id = artifact_id
        mock_artifact.version = 999999
        mock_artifact.title = "High Version Test"
        mock_artifact.content = "Content with high version number"

        # Act
        result = Artifact.from_db(mock_artifact)

        # Assert
        assert result.id == str(artifact_id)
        assert result.version == 999999
        assert result.title == "High Version Test"
        assert result.content == "Content with high version number"

    def test_from_db_with_special_characters_in_title(self, mock_artifact):
        """タイトルに特殊文字を含むテスト"""
        # Arrange
        artifact_id = uuid.uuid4()
        mock_artifact.artifact_id = artifact_id
        mock_artifact.version = 1
        mock_artifact.title = (
            "Title with special chars: !@#$%^&*()_+-=[]{}|;:'\",.<>?/~`"
        )
        mock_artifact.content = "Content for special title test"

        # Act
        result = Artifact.from_db(mock_artifact)

        # Assert
        assert result.id == str(artifact_id)
        assert result.version == 1
        assert (
            result.title == "Title with special chars: !@#$%^&*()_+-=[]{}|;:'\",.<>?/~`"
        )
        assert result.content == "Content for special title test"

    def test_from_db_preserves_uuid_format(self, mock_artifact):
        """UUIDフォーマットが適切に文字列変換されることのテスト"""
        # Arrange
        artifact_id = uuid.UUID("12345678-1234-5678-9abc-123456789abc")
        mock_artifact.artifact_id = artifact_id
        mock_artifact.version = 1
        mock_artifact.title = "UUID Format Test"
        mock_artifact.content = "Testing UUID conversion"

        # Act
        result = Artifact.from_db(mock_artifact)

        # Assert
        assert result.id == "12345678-1234-5678-9abc-123456789abc"
        assert isinstance(result.id, str)
        # 元のUUIDに戻せることを確認
        assert uuid.UUID(result.id) == artifact_id
