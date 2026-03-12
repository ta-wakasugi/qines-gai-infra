import uuid
from unittest.mock import MagicMock, patch
import pytest
from meilisearch_python_sdk import AsyncClient
from sqlalchemy.exc import SQLAlchemyError
from qines_gai_backend.modules.documents.repositories import DocumentRepository
from qines_gai_backend.shared.exceptions import (
    BaseAppError,
    DocumentNotAuthorizedError,
    DocumentNotFoundError,
)


class TestDocumentRepository:
    """DocumentRepositoryのテストクラス"""

    @pytest.fixture
    def mock_meili_client(self):
        """MeilisearchClientのモックを作成"""
        return MagicMock(spec=AsyncClient)

    @pytest.fixture
    def mock_session(self):
        """セッションのモックを作成"""
        return MagicMock()

    @pytest.fixture
    def repository(self, test_data_creator, mock_meili_client):
        """DocumentRepositoryのインスタンスを作成"""
        return DocumentRepository(test_data_creator.session, mock_meili_client)

    @pytest.fixture
    def basic_repository(self, mock_session, mock_meili_client):
        """基本的なDocumentRepositoryのインスタンスを作成"""
        return DocumentRepository(mock_session, mock_meili_client)

    @pytest.fixture
    def sample_document_id(self):
        """サンプルドキュメントIDを作成"""
        return uuid.uuid4()

    @pytest.fixture
    def sample_document_data(self):
        """サンプルドキュメントデータを作成"""
        return {
            "file_name": "test_document.pdf",
            "file_path": "/test/path/test_document.pdf",
            "file_size": 1024,
            "user_id": "test_user_id",
        }

    class TestInit:
        """__init__メソッドのテストクラス"""

        def test_init_success(self, mock_session, mock_meili_client):
            """初期化が正しく実行されることを検証"""
            # Act
            repository = DocumentRepository(mock_session, mock_meili_client)
            # Assert
            assert repository.session is mock_session
            assert repository.meili_client is mock_meili_client

    class TestCreateDocument:
        """create_documentメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_create_document_success(
            self, repository, sample_document_id, sample_document_data
        ):
            """ドキュメント作成が正常に完了することを検証"""
            try:
                # Act
                await repository.create_document(
                    document_id=sample_document_id,
                    content="test document content",
                    **sample_document_data,
                )
                await repository.session.commit()

                # Assert - ドキュメントが作成されたことを検証
                saved_document = await repository.get_document_by_id(
                    str(sample_document_id)
                )
                assert saved_document.document_id == sample_document_id
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_create_document_with_autosar_metadata(self, test_data_creator):
            """AUTOSARメタデータ付きのドキュメント作成が正常に完了することを検証"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                document_id = uuid.uuid4()
                # Act
                await repository.create_document(
                    document_id=document_id,
                    file_name="autosar_doc.pdf",
                    file_path="/autosar/doc.pdf",
                    file_size=2048,
                    content="AUTOSAR document content",
                    user_id="test_user",
                    subject="AUTOSAR",
                    genre="SWS",
                    release="R22-11",
                    is_shared=True,
                )
                await test_data_creator.session.commit()

                # Assert - AUTOSARメタデータが正しく保存されたことを検証
                saved_document = await repository.get_document_by_id(str(document_id))
                assert saved_document.document_id == document_id
                assert saved_document.metadata_info["subject"] == "AUTOSAR"
                assert saved_document.metadata_info["genre"] == "SWS"
                assert saved_document.metadata_info["release"] == "R22-11"
                assert saved_document.is_shared is True
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_create_document_with_optional_metadata_none(
            self, test_data_creator
        ):
            """オプションメタデータがNoneの場合の作成を検証"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                document_id = uuid.uuid4()
                # Act
                await repository.create_document(
                    document_id=document_id,
                    file_name="no_optional_metadata.txt",
                    file_path="/no_optional.txt",
                    file_size=512,
                    content="no optional metadata content",
                    user_id="test_user",
                    subject="others",
                    genre=None,
                    release=None,
                )
                await test_data_creator.session.commit()

                # Assert - オプションメタデータがNoneの場合にmetadata_infoに含まれないことを検証
                saved_document = await repository.get_document_by_id(str(document_id))
                assert saved_document.document_id == document_id
                assert saved_document.metadata_info["subject"] == "others"
                assert "genre" not in saved_document.metadata_info
                assert "release" not in saved_document.metadata_info
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_create_document_with_unknown_file_type(self, test_data_creator):
            """未知のファイル拡張子のMIMEタイプテスト"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                document_id = uuid.uuid4()
                # Act
                await repository.create_document(
                    document_id=document_id,
                    file_name="unknown_file.unknownext",
                    file_path="/unknown.unknownext",
                    file_size=1024,
                    content="unknown file content",
                    user_id="test_user",
                )
                await test_data_creator.session.commit()

                # Assert - 未知の拡張子の場合にフォールバック値が設定されることを検証
                saved_document = await repository.get_document_by_id(str(document_id))
                assert saved_document.document_id == document_id
                assert saved_document.file_type == "application/octet-stream"
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_create_document_database_error(self, test_data_creator):
            """データベースエラーの例外処理を検証"""
            # Arrange
            mock_meili_client = MagicMock(spec=AsyncClient)
            repository = DocumentRepository(
                test_data_creator.session, mock_meili_client
            )
            document_id = uuid.uuid4()
            # Act & Assert
            with patch.object(
                test_data_creator.session, "add", side_effect=Exception("DB Error")
            ):
                with pytest.raises(
                    BaseAppError, match="Failed to save document information"
                ):
                    await repository.create_document(
                        document_id=document_id,
                        file_name="error_doc.pdf",
                        file_path="/error.pdf",
                        file_size=1024,
                        content="test content",
                        user_id="test_user",
                    )

        @pytest.mark.asyncio
        async def test_create_document_with_content_summary_success(
            self, test_data_creator
        ):
            """コンテンツ要約生成が成功する場合のテスト"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                document_id = uuid.uuid4()
                content = "これはテスト用のドキュメント内容です。"
                expected_summary = "テスト用ドキュメントの要約"

                # LLMWrapperとLLMのモック
                mock_llm = MagicMock()
                mock_response = MagicMock()
                mock_response.content = expected_summary
                mock_llm.invoke.return_value = mock_response

                mock_wrapper = MagicMock()
                mock_wrapper.get_llm.return_value = mock_llm

                with patch(
                    "qines_gai_backend.modules.documents.repositories.LLMWrapper",
                    return_value=mock_wrapper,
                ):
                    # Act
                    await repository.create_document(
                        document_id=document_id,
                        file_name="test_summary.pdf",
                        file_path="/test/summary.pdf",
                        file_size=1024,
                        content=content,
                        user_id="test_user",
                        subject="AUTOSAR",
                        genre="SWS",
                        release="R22-11",
                    )

                await test_data_creator.session.commit()

                # Assert - 要約が正しく生成されたことを検証
                saved_document = await repository.get_document_by_id(str(document_id))
                assert saved_document.document_id == document_id
                assert saved_document.summary == expected_summary
                mock_wrapper.get_llm.assert_called_once_with(
                    model_type="azure", temperature=0
                )
                mock_llm.invoke.assert_called_once()
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_create_document_with_content_summary_failure(
            self, test_data_creator
        ):
            """コンテンツ要約生成が失敗する場合のテスト"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                document_id = uuid.uuid4()
                content = "テスト用のコンテンツ"

                # LLMWrapperで例外を発生させる
                mock_wrapper = MagicMock()
                mock_wrapper.get_llm.side_effect = Exception("LLM Error")

                with patch(
                    "qines_gai_backend.modules.documents.repositories.LLMWrapper",
                    return_value=mock_wrapper,
                ):
                    # Act
                    await repository.create_document(
                        document_id=document_id,
                        file_name="test_error.pdf",
                        file_path="/test/error.pdf",
                        file_size=512,
                        content=content,
                        user_id="test_user",
                    )

                await test_data_creator.session.commit()

                # Assert - IDとsummaryフィールドのフォールバックメッセージを検証
                saved_document = await repository.get_document_by_id(str(document_id))
                assert saved_document.document_id == document_id
                assert saved_document.summary == "要約の生成に失敗しました"
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

    class TestGetDocumentById:
        """get_document_by_idメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_document_by_id_success(self, test_data_creator):
            """IDによるドキュメント取得が正常に完了することを検証"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                document_id = await test_data_creator.create_test_document()
                await test_data_creator.session.commit()
                # Act
                result = await repository.get_document_by_id(str(document_id))
                # Assert
                assert result.document_id == document_id
                assert (
                    result.file_name == "test_document.pdf"
                )  # default from TestDataCreator
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_document_by_id_with_user_authorization_success(
            self, test_data_creator
        ):
            """認証チェック付きのドキュメント取得が成功することを検証"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                user_id = "authorized_user"
                document_id = await test_data_creator.create_test_document(
                    user_id=user_id
                )
                await test_data_creator.session.commit()
                # Act
                result = await repository.get_document_by_id(
                    str(document_id), user_id=user_id
                )
                # Assert
                assert result.document_id == document_id
                assert result.user_id == user_id
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_document_by_id_invalid_uuid(self, test_data_creator):
            """無効なUUID形式でDocumentNotFoundErrorが発生することを検証"""
            # Arrange
            mock_meili_client = MagicMock(spec=AsyncClient)
            repository = DocumentRepository(
                test_data_creator.session, mock_meili_client
            )
            # Act & Assert
            with pytest.raises(DocumentNotFoundError):
                await repository.get_document_by_id("invalid-uuid-format")

        @pytest.mark.asyncio
        async def test_get_document_by_id_not_found(self, test_data_creator):
            """存在しないドキュメントIDでDocumentNotFoundErrorが発生することを検証"""
            # Arrange
            mock_meili_client = MagicMock(spec=AsyncClient)
            repository = DocumentRepository(
                test_data_creator.session, mock_meili_client
            )
            nonexistent_id = str(uuid.uuid4())
            # Act & Assert
            with pytest.raises(DocumentNotFoundError):
                await repository.get_document_by_id(nonexistent_id)

        @pytest.mark.asyncio
        async def test_get_document_by_id_not_authorized(self, test_data_creator):
            """権限のないユーザーでDocumentNotAuthorizedErrorが発生することを検証"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                owner_user_id = "owner_user"
                different_user_id = "different_user"
                document_id = await test_data_creator.create_test_document(
                    user_id=owner_user_id
                )
                await test_data_creator.session.commit()
                # Act & Assert
                with pytest.raises(DocumentNotAuthorizedError):
                    await repository.get_document_by_id(
                        str(document_id), user_id=different_user_id
                    )
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_document_by_id_without_user_authorization(
            self, test_data_creator
        ):
            """ユーザー認証チェックなしでのドキュメント取得を検証"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                document_id = await test_data_creator.create_test_document()
                await test_data_creator.session.commit()
                # Act - call without user_id to test the None branch
                result = await repository.get_document_by_id(
                    str(document_id), user_id=None
                )
                # Assert
                assert result.document_id == document_id
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

    class TestGetDocumentWithCollections:
        """get_document_with_collectionsメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_get_document_with_collections_success(self, test_data_creator):
            """コレクション情報付きのドキュメント取得が正常に完了することを検証"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                document_id = await test_data_creator.create_test_document()
                collection_id = await test_data_creator.create_test_collection()
                await test_data_creator.create_test_collection_document(
                    collection_id, document_id
                )
                await test_data_creator.session.commit()
                # Act
                result = await repository.get_document_with_collections(
                    str(document_id)
                )
                # Assert
                assert result.document_id == document_id
                assert len(result.collection_documents) == 1
                assert result.collection_documents[0].collection_id == collection_id
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_document_with_collections_no_collections(
            self, test_data_creator
        ):
            """コレクション関連がないドキュメントの取得を検証"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                document_id = await test_data_creator.create_test_document()
                await test_data_creator.session.commit()
                # Act
                result = await repository.get_document_with_collections(
                    str(document_id)
                )
                # Assert
                assert result.document_id == document_id
                assert len(result.collection_documents) == 0
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_document_with_collections_invalid_uuid(
            self, test_data_creator
        ):
            """無効なUUID形式でDocumentNotFoundErrorが発生することを検証"""
            # Arrange
            mock_meili_client = MagicMock(spec=AsyncClient)
            repository = DocumentRepository(
                test_data_creator.session, mock_meili_client
            )
            # Act & Assert
            with pytest.raises(DocumentNotFoundError):
                await repository.get_document_with_collections("invalid-uuid")

        @pytest.mark.asyncio
        async def test_get_document_with_collections_not_found(self, test_data_creator):
            """存在しないドキュメントIDでDocumentNotFoundErrorが発生することを検証"""
            # Arrange
            mock_meili_client = MagicMock(spec=AsyncClient)
            repository = DocumentRepository(
                test_data_creator.session, mock_meili_client
            )
            nonexistent_id = str(uuid.uuid4())
            # Act & Assert
            with pytest.raises(DocumentNotFoundError):
                await repository.get_document_with_collections(nonexistent_id)

        @pytest.mark.asyncio
        async def test_get_document_with_collections_not_authorized(
            self, test_data_creator
        ):
            """権限のないユーザーでDocumentNotAuthorizedErrorが発生することを検証"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                owner_user_id = "owner_user"
                different_user_id = "different_user"
                document_id = await test_data_creator.create_test_document(
                    user_id=owner_user_id
                )
                await test_data_creator.session.commit()
                # Act & Assert
                with pytest.raises(DocumentNotAuthorizedError):
                    await repository.get_document_with_collections(
                        str(document_id), user_id=different_user_id
                    )
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_document_with_collections_multiple_collections(
            self, test_data_creator
        ):
            """複数のコレクションに属するドキュメントの取得を検証"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                document_id = await test_data_creator.create_test_document()
                collection_id_1 = await test_data_creator.create_test_collection()
                collection_id_2 = await test_data_creator.create_test_collection()
                await test_data_creator.create_test_collection_document(
                    collection_id_1, document_id, position=1
                )
                await test_data_creator.create_test_collection_document(
                    collection_id_2, document_id, position=2
                )
                await test_data_creator.session.commit()
                # Act
                result = await repository.get_document_with_collections(
                    str(document_id)
                )
                # Assert
                assert result.document_id == document_id
                assert len(result.collection_documents) == 2
                collection_ids = [
                    cd.collection_id for cd in result.collection_documents
                ]
                assert collection_id_1 in collection_ids
                assert collection_id_2 in collection_ids
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

        @pytest.mark.asyncio
        async def test_get_document_with_collections_without_user_authorization(
            self, test_data_creator
        ):
            """ユーザー認証チェックなしでのコレクション付きドキュメント取得を検証"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                document_id = await test_data_creator.create_test_document()
                collection_id = await test_data_creator.create_test_collection()
                await test_data_creator.create_test_collection_document(
                    collection_id, document_id
                )
                await test_data_creator.session.commit()
                # Act - call without user_id to test the None branch
                result = await repository.get_document_with_collections(
                    str(document_id), user_id=None
                )
                # Assert
                assert result.document_id == document_id
                assert len(result.collection_documents) == 1
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

    class TestDeleteDocument:
        """delete_documentメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_delete_document_success(self, test_data_creator):
            """ドキュメント削除が正常に完了することを検証"""
            try:
                # Arrange
                mock_meili_client = MagicMock(spec=AsyncClient)
                repository = DocumentRepository(
                    test_data_creator.session, mock_meili_client
                )
                document_id = await test_data_creator.create_test_document()
                await test_data_creator.session.commit()
                # Get document
                document = await repository.get_document_by_id(str(document_id))
                # Act
                await repository.delete_document(document)
                await test_data_creator.session.commit()
                # Assert - verify document is deleted
                with pytest.raises(DocumentNotFoundError):
                    await repository.get_document_by_id(str(document_id))
            except SQLAlchemyError:
                await repository.session.rollback()
                raise

    class TestCommit:
        """commitメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_commit_success(self, test_data_creator):
            """コミットが正常に完了することを検証"""
            # Arrange
            mock_meili_client = MagicMock(spec=AsyncClient)
            repository = DocumentRepository(
                test_data_creator.session, mock_meili_client
            )
            # Act & Assert (verify no exception is raised)
            await repository.commit()

    class TestRollback:
        """rollbackメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_rollback_success(self, test_data_creator):
            """ロールバックが正常に完了することを検証"""
            # Arrange
            mock_meili_client = MagicMock(spec=AsyncClient)
            repository = DocumentRepository(
                test_data_creator.session, mock_meili_client
            )
            # Act & Assert (verify no exception is raised)
            await repository.rollback()
