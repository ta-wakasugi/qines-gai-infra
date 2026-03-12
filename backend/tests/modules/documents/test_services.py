import io
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, mock_open, patch
import pytest
from fastapi import UploadFile
from meilisearch_python_sdk.errors import MeilisearchApiError
from qines_gai_backend.modules.documents.models import (
    DocumentBase,
    SearchDocumentsRequest,
    SearchDocumentsResponse,
    UploadDocumentRequest,
)
from qines_gai_backend.modules.documents.repositories import DocumentRepository
from qines_gai_backend.modules.documents.services import DocumentService
from qines_gai_backend.schemas.schema import T_Document
from qines_gai_backend.shared.exceptions import (
    BaseAppError,
    DocumentNotAuthorizedError,
    DocumentNotFoundError,
    DocumentValidationError,
)


class TestDocumentService:
    """DocumentServiceのテストクラス"""

    @pytest.fixture
    def mock_repository(self):
        """DocumentRepositoryのモックを作成"""
        mock_repo = AsyncMock(spec=DocumentRepository)
        mock_repo.meili_client = AsyncMock()
        return mock_repo

    @pytest.fixture
    def service(self, mock_repository):
        """DocumentServiceのインスタンスを作成"""
        return DocumentService(mock_repository)

    @pytest.fixture
    def mock_upload_file(self):
        """UploadFileのモックを作成"""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test_document.pdf"
        mock_file.size = 1024
        mock_file.file = io.BytesIO(b"mock file content")
        return mock_file

    @pytest.fixture
    def mock_s3_client(self):
        """S3Clientのモックを作成"""
        return MagicMock()

    @pytest.fixture
    def sample_document(self):
        """サンプルドキュメントを作成"""
        document = MagicMock(spec=T_Document)
        document.document_id = uuid.uuid4()
        document.file_name = "sample.pdf"
        document.file_path = "/sample/path.pdf"
        document.file_type = "application/pdf"
        document.file_size = 1024
        document.user_id = "test_user"
        document.is_shared = False
        document.metadata_info = {
            "subject": "AUTOSAR",
            "genre": "SWS",
            "release": "R22-11",
        }
        document.summary = "Sample document summary for testing purposes"
        return document

    class TestInit:
        """__init__メソッドのテストクラス"""

        def test_init_success(self, mock_repository):
            """初期化が正常に実行されることを検証"""
            service = DocumentService(mock_repository)
            assert service.repository is mock_repository

    class TestSearchDocuments:
        """search_documentsメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_search_documents_success(self, service, mock_repository):
            """ドキュメント検索が正常に完了することを検証"""
            # Arrange
            user_id = "test_user"
            request = SearchDocumentsRequest(
                q="test query",
                hits_per_page=5,
                page=1,
                uploader=["user"],
                genre="SWS",
                release="R22-11",
            )
            # MeilSearchレスポンスのモック
            mock_search_result = MagicMock()
            mock_search_result.hits = [
                {
                    "doc_id": "doc-123",
                    "title": "Test Document",
                    "path": "/test/path.pdf",
                    "subject": "AUTOSAR",
                    "genre": "SWS",
                    "release": "R22-11",
                    "file_type": "application/pdf",
                }
            ]
            mock_search_result.total_pages = 1
            mock_index = AsyncMock()
            mock_index.search.return_value = mock_search_result
            mock_repository.meili_client.index = MagicMock(return_value=mock_index)
            # Act
            result = await service.search_documents(user_id, request)
            # Assert
            assert isinstance(result, SearchDocumentsResponse)
            assert result.total_pages == 1
            assert len(result.documents) == 1
            assert result.documents[0].id == "doc-123"
            assert result.documents[0].title == "Test Document"
            # MeilSearchメソッドの呼び出し検証
            mock_repository.meili_client.index.assert_called_once_with("qines-gai")
            mock_index.search.assert_called_once_with(
                query="test query",
                page=1,
                hits_per_page=5,
                filter=[
                    "genre IN [SWS]",
                    "release IN [R22-11]",
                    f"uploader IN [{user_id}]",
                ],
                distinct="doc_id",
            )

        @pytest.mark.asyncio
        async def test_search_documents_with_admin_uploader(
            self, service, mock_repository
        ):
            """アップローダーがadminを含む場合のテスト"""
            # Arrange
            user_id = "test_user"
            request = SearchDocumentsRequest(uploader=["admin"])
            mock_search_result = MagicMock()
            mock_search_result.hits = []
            mock_search_result.total_pages = 0
            mock_index = AsyncMock()
            mock_index.search.return_value = mock_search_result
            mock_repository.meili_client.index = MagicMock(return_value=mock_index)
            # Act
            await service.search_documents(user_id, request)
            # Assert - adminがそのまま使用される
            mock_index.search.assert_called_once()
            call_args = mock_index.search.call_args
            filters = call_args.kwargs["filter"]
            assert "uploader IN [admin]" in filters

        @pytest.mark.asyncio
        async def test_search_documents_with_user_uploader(
            self, service, mock_repository
        ):
            """アップローダーがuserを含む場合のテスト"""
            # Arrange
            user_id = "test_user"
            request = SearchDocumentsRequest(uploader=["user"])
            mock_search_result = MagicMock()
            mock_search_result.hits = []
            mock_search_result.total_pages = 0
            mock_index = AsyncMock()
            mock_index.search.return_value = mock_search_result
            mock_repository.meili_client.index = MagicMock(return_value=mock_index)
            # Act
            await service.search_documents(user_id, request)
            # Assert - userがuser_idに変換される
            call_args = mock_index.search.call_args
            filters = call_args.kwargs["filter"]
            assert f"uploader IN [{user_id}]" in filters

        @pytest.mark.asyncio
        async def test_search_documents_with_others_subject(
            self, service, mock_repository
        ):
            """subjectがothersの場合にジャンルとリリースがNullになることをテスト"""
            # Arrange
            user_id = "test_user"
            request = SearchDocumentsRequest()
            mock_search_result = MagicMock()
            mock_search_result.hits = [
                {
                    "doc_id": "doc-456",
                    "title": "Others Document",
                    "path": "/others/path.txt",
                    "subject": "others",
                    "genre": "SomeGenre",
                    "release": "V1.0",
                    "file_type": "text/plain",
                }
            ]
            mock_search_result.total_pages = 1
            mock_index = AsyncMock()
            mock_index.search.return_value = mock_search_result
            mock_repository.meili_client.index = MagicMock(return_value=mock_index)
            # Act
            result = await service.search_documents(user_id, request)
            # Assert - othersの場合genre/releaseはNoneになる
            assert result.documents[0].genre is None
            assert result.documents[0].release is None

        @pytest.mark.asyncio
        async def test_search_documents_meilisearch_api_error(
            self, service, mock_repository
        ):
            """MeilSearchAPIエラーの場合の例外処理を検証"""
            # Arrange
            user_id = "test_user"
            request = SearchDocumentsRequest()
            mock_index = AsyncMock()
            from unittest.mock import MagicMock

            response_mock = MagicMock()
            response_mock.status_code = 400
            mock_index.search.side_effect = MeilisearchApiError(
                "API Error", response=response_mock
            )
            mock_repository.meili_client.index = MagicMock(return_value=mock_index)
            # Act & Assert
            with pytest.raises(MeilisearchApiError):
                await service.search_documents(user_id, request)

        @pytest.mark.asyncio
        async def test_search_documents_general_error(self, service, mock_repository):
            """一般的なエラーの場合の例外処理を検証"""
            # Arrange
            user_id = "test_user"
            request = SearchDocumentsRequest()
            mock_index = AsyncMock()
            mock_index.search.side_effect = Exception("General Error")
            mock_repository.meili_client.index = MagicMock(return_value=mock_index)
            # Act & Assert
            with pytest.raises(BaseAppError, match="Failed to search documents"):
                await service.search_documents(user_id, request)

        @pytest.mark.asyncio
        async def test_search_documents_no_filters(self, service, mock_repository):
            """フィルタが指定されていない場合のテスト"""
            # Arrange
            user_id = "test_user"
            request = SearchDocumentsRequest()
            mock_search_result = MagicMock()
            mock_search_result.hits = []
            mock_search_result.total_pages = 0
            mock_index = AsyncMock()
            mock_index.search.return_value = mock_search_result
            mock_repository.meili_client.index = MagicMock(return_value=mock_index)
            # Act
            await service.search_documents(user_id, request)
            # Assert - デフォルトのuploaderフィルタのみ適用される
            call_args = mock_index.search.call_args
            filters = call_args.kwargs["filter"]
            assert len(filters) == 1  # uploaderフィルタのみ
            assert f"uploader IN [{user_id},admin]" in filters

    class TestUploadDocument:
        """upload_documentメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_upload_document_success(
            self,
            service,
            mock_repository,
            mock_upload_file,
            mock_s3_client,
            sample_document,
        ):
            """ドキュメントアップロードが正常に完了することを検証（統合テスト）"""
            # Arrange
            user_id = "test_user"
            request = UploadDocumentRequest(
                subject="AUTOSAR", genre="SWS", release="R22-11"
            )
            mock_repository.create_document.return_value = sample_document
            mock_repository.commit.return_value = None

            # プロセッサが返すDocumentのモック
            from langchain.docstore.document import Document

            mock_documents = [
                Document(
                    page_content="テスト内容",
                    metadata={"page_num": 1, "total_pages": 1},
                )
            ]

            # Meilisearchインデックスのモック
            mock_index = AsyncMock()
            mock_repository.meili_client.index = MagicMock(return_value=mock_index)

            # プロセッサのモック
            mock_processor = MagicMock()
            mock_processor.process.return_value = mock_documents

            with patch.dict(os.environ, {"S3_BUCKET_NAME": "test-bucket"}):
                with patch(
                    "qines_gai_backend.modules.documents.services.get_processor"
                ) as mock_get_processor:
                    mock_get_processor.return_value = mock_processor
                    with patch(
                        "qines_gai_backend.modules.documents.services.RecursiveCharacterTextSplitter"
                    ) as mock_splitter_class:
                        mock_splitter = MagicMock()
                        mock_splitter.split_documents.return_value = []  # チャンクなし
                        mock_splitter_class.return_value = mock_splitter

                        with patch("os.unlink"):  # 一時ファイル削除をモック
                            # Act - privateメソッドは実際に動く
                            result = await service.upload_document(
                                file=mock_upload_file,
                                user_id=user_id,
                                request=request,
                                s3_client=mock_s3_client,
                            )

            # Assert - 実際の処理が走ったことを検証
            assert isinstance(result, DocumentBase)
            mock_s3_client.upload_fileobj.assert_called_once()  # S3アップロードが実行された
            mock_get_processor.assert_called_once_with(".pdf")  # プロセッサが呼ばれた
            mock_repository.create_document.assert_called_once()  # DBに保存された
            mock_repository.commit.assert_called_once()  # コミットされた

        @pytest.mark.asyncio
        async def test_upload_document_validation_error(
            self, service, mock_upload_file, mock_s3_client
        ):
            """ファイル検証エラーの場合の例外処理を検証"""
            # Arrange
            user_id = "test_user"
            request = UploadDocumentRequest()
            with patch.object(
                service,
                "_validate_file",
                side_effect=DocumentValidationError("Invalid file"),
            ):
                # Act & Assert
                with pytest.raises(DocumentValidationError, match="Invalid file"):
                    await service.upload_document(
                        file=mock_upload_file,
                        user_id=user_id,
                        request=request,
                        s3_client=mock_s3_client,
                    )

        @pytest.mark.asyncio
        async def test_upload_document_storage_error(
            self, service, mock_repository, mock_upload_file, mock_s3_client
        ):
            """ストレージアップロードエラーの場合の例外処理を検証"""
            # Arrange
            user_id = "test_user"
            request = UploadDocumentRequest()
            with patch.dict(os.environ, {"S3_BUCKET_NAME": "test-bucket"}):
                with patch.object(service, "_validate_file"):
                    with patch.object(
                        service,
                        "_upload_to_storage",
                        side_effect=BaseAppError("Storage error"),
                    ):
                        with patch.object(
                            service, "_cleanup_resources"
                        ) as mock_cleanup:
                            # Act & Assert
                            with pytest.raises(BaseAppError, match="Storage error"):
                                await service.upload_document(
                                    file=mock_upload_file,
                                    user_id=user_id,
                                    request=request,
                                    s3_client=mock_s3_client,
                                )
            # クリーンアップが呼び出されることを検証
            mock_cleanup.assert_called_once()
            mock_repository.rollback.assert_called_once()

    class TestDeleteDocument:
        """delete_documentメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_delete_document_success(
            self, service, mock_repository, mock_s3_client, sample_document
        ):
            """ドキュメント削除が正常に完了することを検証"""
            # Arrange
            document_id = str(sample_document.document_id)
            user_id = "test_user"
            mock_repository.get_document_with_collections.return_value = sample_document
            # MeilSearchモックの設定
            mock_task = MagicMock()
            mock_task.task_uid = "task-123"
            mock_index = AsyncMock()
            mock_index.delete_documents_by_filter.return_value = mock_task
            mock_repository.meili_client.index = MagicMock(return_value=mock_index)
            mock_repository.meili_client.wait_for_task.return_value = None
            with patch.object(service, "_delete_from_storage") as mock_delete_storage:
                # Act
                await service.delete_document(document_id, user_id, mock_s3_client)
            # Assert
            mock_repository.get_document_with_collections.assert_called_once_with(
                document_id, user_id
            )
            mock_index.delete_documents_by_filter.assert_called_once_with(
                filter=[f"doc_id = '{document_id}'", f"uploader = '{user_id}'"]
            )
            mock_repository.meili_client.wait_for_task.assert_called_once_with(
                "task-123", raise_for_status=True
            )
            mock_repository.delete_document.assert_called_once_with(sample_document)
            mock_repository.commit.assert_called_once()
            mock_delete_storage.assert_called_once_with(
                sample_document, user_id, mock_s3_client
            )

        @pytest.mark.asyncio
        async def test_delete_document_not_found(
            self, service, mock_repository, mock_s3_client
        ):
            """ドキュメントが見つからない場合の例外処理を検証"""
            # Arrange
            document_id = str(uuid.uuid4())
            user_id = "test_user"
            mock_repository.get_document_with_collections.side_effect = (
                DocumentNotFoundError()
            )
            # Act & Assert
            with pytest.raises(DocumentNotFoundError):
                await service.delete_document(document_id, user_id, mock_s3_client)
            mock_repository.rollback.assert_called_once()

        @pytest.mark.asyncio
        async def test_delete_document_not_authorized(
            self, service, mock_repository, mock_s3_client
        ):
            """権限がない場合の例外処理を検証"""
            # Arrange
            document_id = str(uuid.uuid4())
            user_id = "test_user"
            mock_repository.get_document_with_collections.side_effect = (
                DocumentNotAuthorizedError()
            )
            # Act & Assert
            with pytest.raises(DocumentNotAuthorizedError):
                await service.delete_document(document_id, user_id, mock_s3_client)
            mock_repository.rollback.assert_called_once()

        @pytest.mark.asyncio
        async def test_delete_document_general_error(
            self, service, mock_repository, mock_s3_client, sample_document
        ):
            """一般的なエラーの場合の例外処理を検証"""
            # Arrange
            document_id = str(sample_document.document_id)
            user_id = "test_user"
            mock_repository.get_document_with_collections.return_value = sample_document
            mock_repository.meili_client.index = MagicMock(
                side_effect=Exception("General error")
            )
            # Act & Assert
            with pytest.raises(BaseAppError, match="Failed to delete document"):
                await service.delete_document(document_id, user_id, mock_s3_client)
            mock_repository.rollback.assert_called_once()

    class TestValidateFile:
        """_validate_fileメソッドのテストクラス"""

        def test_validate_file_success(self, service):
            """正常なファイルの検証が通ることを検証"""
            # Arrange
            mock_file = MagicMock(spec=UploadFile)
            mock_file.filename = "test.pdf"
            mock_file.file = io.BytesIO(b"test content")
            # Act & Assert (例外が発生しないことを検証)
            service._validate_file(mock_file)

        def test_validate_file_empty_file(self, service):
            """空ファイルの場合にDocumentValidationErrorが発生することを検証"""
            # Arrange
            mock_file = MagicMock(spec=UploadFile)
            mock_file.filename = "empty.pdf"
            mock_file.file = io.BytesIO(b"")
            # Act & Assert
            with pytest.raises(DocumentValidationError, match="Empty file provided"):
                service._validate_file(mock_file)

        def test_validate_file_too_large(self, service):
            """サイズ超過ファイルの場合にDocumentValidationErrorが発生することを検証"""
            # Arrange
            mock_file = MagicMock(spec=UploadFile)
            mock_file.filename = "large.pdf"
            large_content = b"x" * (6 * 1024 * 1024)  # 6MB
            mock_file.file = io.BytesIO(large_content)
            # Act & Assert
            with pytest.raises(
                DocumentValidationError, match="File size exceeds maximum limit"
            ):
                service._validate_file(mock_file)

        def test_validate_file_no_extension(self, service):
            """拡張子なしファイルの場合にDocumentValidationErrorが発生することを検証"""
            # Arrange
            mock_file = MagicMock(spec=UploadFile)
            mock_file.filename = "noextension"
            mock_file.file = io.BytesIO(b"test content")
            # Act & Assert
            with pytest.raises(
                DocumentValidationError, match="File extension not found"
            ):
                service._validate_file(mock_file)

        def test_validate_file_unsupported_extension(self, service):
            """未対応拡張子の場合にDocumentValidationErrorが発生することを検証"""
            # Arrange
            mock_file = MagicMock(spec=UploadFile)
            mock_file.filename = "test.exe"
            mock_file.file = io.BytesIO(b"test content")
            # Act & Assert
            with pytest.raises(DocumentValidationError, match="Unsupported file type"):
                service._validate_file(mock_file)

    class TestUploadToStorage:
        """_upload_to_storageメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_upload_to_storage_s3_success(self, service, mock_s3_client):
            """S3への正常アップロードを検証"""
            # Arrange
            file_content = b"test content"
            bucket_name = "test-bucket"
            s3_path = "test/path/file.pdf"
            # Act
            result = await service._upload_to_storage(
                file_content, bucket_name, s3_path, mock_s3_client
            )
            # Assert
            assert result == f"/{bucket_name}/{s3_path}"
            mock_s3_client.upload_fileobj.assert_called_once()

        @pytest.mark.asyncio
        async def test_upload_to_storage_error(self, service, mock_s3_client):
            """ストレージアップロードエラーの場合の例外処理を検証"""
            # Arrange
            file_content = b"test content"
            bucket_name = "test-bucket"
            s3_path = "test/path/file.pdf"
            mock_s3_client.upload_fileobj.side_effect = Exception("Upload error")
            # Act & Assert
            with pytest.raises(
                BaseAppError, match="Failed to upload file to storage"
            ):
                await service._upload_to_storage(
                    file_content, bucket_name, s3_path, mock_s3_client
                )

    class TestProcessAndIndexDocument:
        """_process_and_index_documentメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_process_and_index_document_success(
            self, service, mock_repository
        ):
            """ドキュメント処理とチャンク分割インデックス作成が正常に完了することを検証"""
            # Arrange
            file_content = b"test pdf content"
            filename = "test.pdf"
            document_id = uuid.uuid4()
            file_path = "/test/path.pdf"
            user_id = "test_user"
            request = UploadDocumentRequest(
                subject="AUTOSAR", genre="SWS", release="R22-11"
            )

            # プロセッサが返すDocumentのモック
            from langchain.docstore.document import Document

            mock_doc1 = Document(
                page_content="ドキュメント1の内容",
                metadata={"page_num": 1, "total_pages": 2},
            )
            mock_doc2 = Document(
                page_content="ドキュメント2の内容",
                metadata={"page_num": 2, "total_pages": 2},
            )
            mock_documents = [mock_doc1, mock_doc2]

            # チャンク分割後のモック
            mock_chunk1 = Document(
                page_content="チャンク1の内容",
                metadata={"page_num": 1, "total_pages": 2},
            )
            mock_chunk2 = Document(
                page_content="チャンク2の内容",
                metadata={"page_num": 2, "total_pages": 2},
            )
            mock_chunks = [mock_chunk1, mock_chunk2]

            mock_index = AsyncMock()
            mock_repository.meili_client.index = MagicMock(return_value=mock_index)

            # プロセッサのモック
            mock_processor = MagicMock()
            mock_processor.process.return_value = mock_documents

            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                mock_temp_file = MagicMock()
                mock_temp_file.name = "/tmp/temp_file.pdf"
                mock_temp_file.__enter__.return_value = mock_temp_file
                mock_temp.return_value = mock_temp_file

                with patch(
                    "qines_gai_backend.modules.documents.services.get_processor"
                ) as mock_get_processor:
                    mock_get_processor.return_value = mock_processor

                    with patch(
                        "qines_gai_backend.modules.documents.services.RecursiveCharacterTextSplitter"
                    ) as mock_splitter_class:
                        mock_splitter = MagicMock()
                        mock_splitter.split_documents.return_value = mock_chunks
                        mock_splitter_class.return_value = mock_splitter

                        with patch("os.unlink") as mock_unlink:
                            # Act
                            result = await service._process_and_index_document(
                                file_content,
                                filename,
                                document_id,
                                file_path,
                                user_id,
                                request,
                            )

            # Assert - 戻り値の検証
            assert result == "ドキュメント1の内容\n\nドキュメント2の内容"

            # Assert - 外部ライブラリが正しく呼び出されているか
            mock_temp_file.write.assert_called_once_with(file_content)
            mock_get_processor.assert_called_once_with(".pdf")
            mock_processor.process.assert_called_once_with("/tmp/temp_file.pdf")
            mock_splitter.split_documents.assert_called_once_with(mock_documents)
            mock_unlink.assert_called_once_with("/tmp/temp_file.pdf")

            # Assert - チャンクが正しく生成されMeilisearchに送信されたことを検証
            mock_index.add_documents.assert_called_once()
            add_documents_call = mock_index.add_documents.call_args[0][0]

            # チャンク数と重要なフィールドのみ検証
            assert len(add_documents_call) == 2
            assert add_documents_call[0]["id"] == f"{document_id}_c0"
            assert add_documents_call[0]["contents"] == "チャンク1の内容"
            assert add_documents_call[0]["chunk_num"] == 1
            assert add_documents_call[1]["id"] == f"{document_id}_c1"
            assert add_documents_call[1]["contents"] == "チャンク2の内容"
            assert add_documents_call[1]["chunk_num"] == 2

        @pytest.mark.asyncio
        async def test_process_and_index_document_temp_file_cleanup_error(
            self, service, mock_repository
        ):
            """finallyブロックでの一時ファイル削除例外処理のテスト"""
            # Arrange
            file_content = b"test pdf content"
            filename = "test.pdf"
            document_id = uuid.uuid4()
            file_path = "/test/path.pdf"
            user_id = "test_user"
            request = UploadDocumentRequest(
                subject="AUTOSAR", genre="SWS", release="R22-11"
            )

            from langchain.docstore.document import Document

            mock_documents = [
                Document(
                    page_content="短いコンテンツ",
                    metadata={"page_num": 1, "total_pages": 1},
                )
            ]

            mock_index = AsyncMock()
            mock_repository.meili_client.index = MagicMock(return_value=mock_index)

            # プロセッサのモック
            mock_processor = MagicMock()
            mock_processor.process.return_value = mock_documents

            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                mock_temp_file = MagicMock()
                mock_temp_file.name = "/tmp/temp_file.pdf"
                mock_temp_file.__enter__.return_value = mock_temp_file
                mock_temp.return_value = mock_temp_file

                with patch(
                    "qines_gai_backend.modules.documents.services.get_processor"
                ) as mock_get_processor:
                    mock_get_processor.return_value = mock_processor

                    with patch(
                        "qines_gai_backend.modules.documents.services.RecursiveCharacterTextSplitter"
                    ) as mock_splitter_class:
                        mock_splitter = MagicMock()
                        mock_splitter.split_documents.return_value = []
                        mock_splitter_class.return_value = mock_splitter

                        # os.unlinkでC0カバレッジのfinallyブロック例外処理をテスト
                        with patch(
                            "os.unlink", side_effect=Exception("File deletion error")
                        ) as mock_unlink:
                            with patch(
                                "qines_gai_backend.modules.documents.services.logger"
                            ) as mock_logger:
                                # Act
                                await service._process_and_index_document(
                                    file_content,
                                    filename,
                                    document_id,
                                    file_path,
                                    user_id,
                                    request,
                                )

            # Assert - 一時ファイルクリーンアップ失敗時の警告ログが出力されたことを検証
            mock_unlink.assert_called_once_with("/tmp/temp_file.pdf")
            mock_logger.warning.assert_called_once()
            warning_call_args = str(mock_logger.warning.call_args)
            assert "Failed to remove temporary file" in warning_call_args
            assert "/tmp/temp_file.pdf" in warning_call_args

        @pytest.mark.asyncio
        async def test_process_and_index_document_markitdown_error(
            self, service, mock_repository
        ):
            """プロセッサでの例外処理を検証"""
            # Arrange
            file_content = b"test content"
            filename = "test.pdf"
            document_id = uuid.uuid4()
            file_path = "/test/path.pdf"
            user_id = "test_user"
            request = UploadDocumentRequest()

            # プロセッサのモック（例外を発生させる）
            mock_processor = MagicMock()
            mock_processor.process.side_effect = Exception("Processor error")

            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                mock_temp_file = MagicMock()
                mock_temp_file.name = "/tmp/temp_file.pdf"
                mock_temp_file.__enter__.return_value = mock_temp_file
                mock_temp.return_value = mock_temp_file

                with patch(
                    "qines_gai_backend.modules.documents.services.get_processor"
                ) as mock_get_processor:
                    mock_get_processor.return_value = mock_processor

                    with patch("os.unlink"):
                        # Act & Assert
                        with pytest.raises(
                            BaseAppError, match="Failed to index document"
                        ):
                            await service._process_and_index_document(
                                file_content,
                                filename,
                                document_id,
                                file_path,
                                user_id,
                                request,
                            )

        @pytest.mark.asyncio
        async def test_process_and_index_document_empty_chunks(
            self, service, mock_repository
        ):
            """チャンクが空の場合のテスト"""
            # Arrange
            file_content = b"test content"
            filename = "test.pdf"
            document_id = uuid.uuid4()
            file_path = "/test/path.pdf"
            user_id = "test_user"
            request = UploadDocumentRequest()

            from langchain.docstore.document import Document

            mock_documents = [
                Document(
                    page_content="short content",
                    metadata={"page_num": 1, "total_pages": 1},
                )
            ]

            mock_index = AsyncMock()
            mock_repository.meili_client.index = MagicMock(return_value=mock_index)

            # プロセッサのモック
            mock_processor = MagicMock()
            mock_processor.process.return_value = mock_documents

            # 空のチャンクリストを返すモック
            empty_chunks = []

            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                mock_temp_file = MagicMock()
                mock_temp_file.name = "/tmp/temp_file.pdf"
                mock_temp_file.__enter__.return_value = mock_temp_file
                mock_temp.return_value = mock_temp_file

                with patch(
                    "qines_gai_backend.modules.documents.services.get_processor"
                ) as mock_get_processor:
                    mock_get_processor.return_value = mock_processor

                    with patch(
                        "qines_gai_backend.modules.documents.services.RecursiveCharacterTextSplitter"
                    ) as mock_splitter_class:
                        mock_splitter = MagicMock()
                        mock_splitter.split_documents.return_value = empty_chunks
                        mock_splitter_class.return_value = mock_splitter

                        with patch("os.unlink"):
                            # Act
                            result = await service._process_and_index_document(
                                file_content,
                                filename,
                                document_id,
                                file_path,
                                user_id,
                                request,
                            )

            # Assert - 戻り値の検証
            assert result == "short content"
            # Assert - add_documentsが呼ばれないことを検証
            mock_index.add_documents.assert_not_called()

    class TestDeleteFromStorage:
        """_delete_from_storageメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_delete_from_storage_s3_success(
            self, service, sample_document, mock_s3_client
        ):
            """S3からの削除が正常に完了することを検証"""
            # Arrange
            user_id = "test_user"
            mock_waiter = MagicMock()
            mock_s3_client.get_waiter.return_value = mock_waiter
            with patch.dict(os.environ, {"S3_BUCKET_NAME": "test-bucket"}):
                # Act
                await service._delete_from_storage(
                    sample_document, user_id, mock_s3_client
                )
            # Assert
            expected_key = (
                f"{user_id}/{sample_document.document_id}/{sample_document.file_name}"
            )
            mock_s3_client.delete_object.assert_called_once_with(
                Bucket="test-bucket", Key=expected_key
            )
            mock_waiter.wait.assert_called_once_with(
                Bucket="test-bucket", Key=expected_key
            )

        @pytest.mark.asyncio
        async def test_delete_from_storage_error_handling(
            self, service, sample_document, mock_s3_client
        ):
            """ストレージ削除エラーの場合に例外を発生させないことを検証"""
            # Arrange
            user_id = "test_user"
            mock_s3_client.delete_object.side_effect = Exception("Delete error")
            with patch.dict(os.environ, {"S3_BUCKET_NAME": "test-bucket"}):
                # Act & Assert (例外が発生しないことを検証)
                await service._delete_from_storage(
                    sample_document, user_id, mock_s3_client
                )

    class TestCleanupResources:
        """_cleanup_resourcesメソッドのテストクラス"""

        @pytest.mark.asyncio
        async def test_cleanup_resources_success(
            self, service, mock_repository, mock_s3_client
        ):
            """リソースクリーンアップが正常に完了することを検証"""
            # Arrange
            bucket_name = "test-bucket"
            s3_path = "test/path/file.pdf"
            document_id = uuid.uuid4()
            mock_index = AsyncMock()
            mock_repository.meili_client.index = MagicMock(return_value=mock_index)
            # Act
            await service._cleanup_resources(
                mock_s3_client, bucket_name, s3_path, document_id
            )
            # Assert
            mock_s3_client.delete_object.assert_called_once_with(
                Bucket=bucket_name, Key=s3_path
            )
            mock_index.delete_document.assert_called_once_with(str(document_id))

        @pytest.mark.asyncio
        async def test_cleanup_resources_with_errors(
            self, service, mock_repository, mock_s3_client
        ):
            """クリーンアップでエラーが発生しても例外を発生させないことを検証"""
            # Arrange
            bucket_name = "test-bucket"
            s3_path = "test/path/file.pdf"
            document_id = uuid.uuid4()
            mock_s3_client.delete_object.side_effect = Exception("S3 delete error")
            mock_index = AsyncMock()
            mock_index.delete_document.side_effect = Exception(
                "Meilisearch delete error"
            )
            mock_repository.meili_client.index = MagicMock(return_value=mock_index)
            # Act & Assert (例外が発生しないことを検証)
            await service._cleanup_resources(
                mock_s3_client, bucket_name, s3_path, document_id
            )
