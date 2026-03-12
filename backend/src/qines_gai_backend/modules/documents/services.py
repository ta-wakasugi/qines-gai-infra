import mimetypes
import os
import tempfile
import uuid
from io import BytesIO
from pathlib import Path as FilePath

from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from meilisearch_python_sdk.errors import MeilisearchApiError
from mypy_boto3_s3 import S3Client

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.documents.models import (
    DocumentBase,
    MeilisearchChunk,
    SearchDocumentsRequest,
    SearchDocumentsResponse,
    UploadDocumentRequest,
)
from qines_gai_backend.modules.documents.processors import get_processor
from qines_gai_backend.modules.documents.repositories import DocumentRepository
from qines_gai_backend.shared.exceptions import (
    BaseAppError,
    DocumentNotAuthorizedError,
    DocumentNotFoundError,
    DocumentValidationError,
)

logger = get_logger(__name__)


class DocumentService:
    """ドキュメント関連のビジネスロジック層"""

    def __init__(self, repository: DocumentRepository):
        """DocumentServiceを初期化する。

        Args:
            repository (DocumentRepository): ドキュメントデータアクセス用リポジトリ
        """
        self.repository = repository

    @log_function_start_end
    async def search_documents(
        self,
        user_id: str,
        request: SearchDocumentsRequest,
    ) -> SearchDocumentsResponse:
        """MeilSearchを使用してドキュメントを検索する。

        Args:
            user_id (str): 検索を実行するユーザーID
            request (SearchDocumentsRequest): 検索リクエストパラメータ

        Returns:
            SearchDocumentsResponse: 検索結果とメタデータ

        Raises:
            BaseAppError: 検索処理中にエラーが発生した場合
        """
        try:
            # インデックスを取得する
            index = self.repository.meili_client.index("qines-gai")

            # フィルターの設定
            filters = []
            if request.genre:
                filters.append(f"genre IN [{request.genre}]")
            if request.release:
                filters.append(f"release IN [{request.release}]")
            if request.uploader:
                uploader_list = [
                    user_id if u == "user" else u for u in request.uploader
                ]
                uploader_str = ",".join(uploader_list)
                filters.append(f"uploader IN [{uploader_str}]")

            # パラメータを設定し、検索を実行する
            meilisearch_results = await index.search(
                query=request.q,
                page=request.page,
                hits_per_page=request.hits_per_page,
                filter=filters,
                distinct="doc_id",
            )

            

            # ドキュメントリストを作成する
            documents = [
                DocumentBase(
                    id=hit["doc_id"],
                    title=hit["title"],
                    path=hit["path"],
                    subject=hit["subject"],
                    genre=hit["genre"] if hit["subject"] == "AUTOSAR" else None,
                    release=hit["release"] if hit["subject"] == "AUTOSAR" else None,
                    file_type=hit["file_type"],
                    contents=hit.get("contents") # meilSearchでヒットしたチャンク検索結果を入れる
                )
                for hit in meilisearch_results.hits
            ]

            # 検索結果をレスポンスモデルにマッピング
            return SearchDocumentsResponse(
                total_pages=meilisearch_results.total_pages,
                documents=documents,
            )
        except MeilisearchApiError as e:
            logger.error(f"Error searching documents: {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise BaseAppError("Failed to search documents")

    @log_function_start_end
    async def upload_document(
        self,
        file: UploadFile,
        user_id: str,
        request: UploadDocumentRequest,
        s3_client: S3Client,
    ) -> DocumentBase:
        """ドキュメントをアップロードし、データベースとMeilSearchに登録する。

        Args:
            file (UploadFile): アップロード対象のファイル
            user_id (str): アップロードするユーザーID
            request (UploadDocumentRequest): アップロードリクエストパラメータ
            s3_client (S3Client): S3クライアント

        Returns:
            DocumentBase: 作成されたドキュメントの基本情報

        Raises:
            DocumentValidationError: ファイルバリデーションエラー
            BaseAppError: アップロード処理中にエラーが発生した場合

        Note:
            ファイルはストレージに保存され、DoclingでパースされてMeilSearchにインデックスされる
        """

        # ファイルバリデーション
        self._validate_file(file)

        # S3保存のための準備
        bucket_name = os.getenv("S3_BUCKET_NAME")
        document_id = uuid.uuid4()
        s3_path = f"{user_id}/{document_id}/{file.filename}"

        try:
            # ファイルの内容を一度メモリに保持
            file_content = file.file.read()
            file.file.seek(0)

            # S3へのアップロード
            file_path = await self._upload_to_storage(
                file_content, bucket_name, s3_path, s3_client
            )

            # ファイルのパースとMeilisearchへの登録
            parsed_content = await self._process_and_index_document(
                file_content, file.filename, document_id, file_path, user_id, request
            )

            # データベースへの保存
            document = await self.repository.create_document(
                document_id=document_id,
                file_name=file.filename,
                file_path=file_path,
                file_size=file.size,
                content=parsed_content,
                user_id=user_id,
                subject=request.subject,
                genre=request.genre,
                release=request.release,
            )

            # commit前にPydanticモデルに変換
            result = DocumentBase.from_db(document)

            await self.repository.commit()
            return result

        except Exception as e:
            await self.repository.rollback()
            # クリーンアップ処理
            await self._cleanup_resources(s3_client, bucket_name, s3_path, document_id)
            logger.error(f"Error uploading document: {e}")
            # raise BaseAppError("Failed to upload document")
            raise

    @log_function_start_end
    async def delete_document(
        self,
        document_id: str,
        user_id: str,
        s3_client: S3Client,
    ) -> None:
        """ドキュメントをデータベース、MeilSearch、ストレージから完全に削除する。

        Args:
            document_id (str): 削除対象のドキュメントID
            user_id (str): 削除を実行するユーザーID
            s3_client (S3Client): S3クライアント

        Raises:
            DocumentNotFoundError: ドキュメントが存在しない場合
            DocumentNotAuthorizedError: ユーザーに権限がない場合
            BaseAppError: 削除処理中にエラーが発生した場合

        Note:
            関連するコレクションや会話履歴にも影響するため注意が必要
        """
        try:
            # ドキュメント存在確認と権限チェック
            document = await self.repository.get_document_with_collections(
                document_id, user_id
            )

            # Meilisearchから削除
            index = self.repository.meili_client.index("qines-gai")
            task = await index.delete_documents_by_filter(
                filter=[f"doc_id = '{document_id}'", f"uploader = '{user_id}'"]
            )
            await self.repository.meili_client.wait_for_task(
                task.task_uid, raise_for_status=True
            )

            # データベースから削除
            await self.repository.delete_document(document)
            await self.repository.commit()

            # S3から削除
            await self._delete_from_storage(document, user_id, s3_client)

        except (DocumentNotFoundError, DocumentNotAuthorizedError):
            await self.repository.rollback()
            raise
        except Exception as e:
            await self.repository.rollback()
            logger.error(f"Error deleting document: {e}")
            raise BaseAppError("Failed to delete document")

    def _validate_file(self, file: UploadFile) -> None:
        """アップロードされたファイルのサイズ、形式、内容をバリデーションする。

        Args:
            file (UploadFile): バリデーション対象のファイル

        Raises:
            DocumentValidationError: ファイルが無効な場合（サイズ超過、非対応形式等）
        """
        MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2GB
        ALLOWED_EXTENSIONS = {
            ".pdf",
            ".docx",
            ".xlsx",
            ".pptx",
            ".md",
            ".adoc",
            ".html",
            ".xhtml",
            ".xls",
        }

        # ファイルサイズの確認
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        if size == 0:
            raise DocumentValidationError("Empty file provided")

        if size > MAX_FILE_SIZE_BYTES:
            raise DocumentValidationError(
                f"File size exceeds maximum limit of {MAX_FILE_SIZE_BYTES} bytes"
            )

        # ファイル形式チェック
        file_extension = FilePath(file.filename).suffix.lower()
        if not file_extension:
            raise DocumentValidationError("File extension not found")
        if file_extension not in ALLOWED_EXTENSIONS:
            raise DocumentValidationError(
                f"Unsupported file type. Supported file types are: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

    async def _upload_to_storage(
        self, file_content: bytes, bucket_name: str, s3_path: str, s3_client: S3Client
    ) -> str:
        """ファイルをS3にアップロードする。

        Args:
            file_content (bytes): アップロードするファイルのバイナリデータ
            bucket_name (str): S3バケット名
            s3_path (str): S3内の保存パス
            s3_client (S3Client): S3クライアント

        Returns:
            str: ファイルの保存パス

        Raises:
            BaseAppError: アップロードに失敗した場合
        """
        try:
            s3_client.upload_fileobj(
                BytesIO(file_content),
                bucket_name,
                s3_path,
            )
            return f"/{bucket_name}/{s3_path}"
        except Exception as e:
            logger.error(f"Failed to upload file to storage: {str(e)}")
            raise BaseAppError("Failed to upload file to storage")

    async def _process_and_index_document(
        self,
        file_content: bytes,
        filename: str,
        document_id: uuid.UUID,
        file_path: str,
        user_id: str,
        request: UploadDocumentRequest,
    ) -> str:
        """MarkItDownでドキュメントをパースし、チャンク分割してMeilSearchにインデックスを作成する。

        Args:
            file_content (bytes): 処理対象のファイルバイナリデータ
            filename (str): ファイル名
            document_id (uuid.UUID): ドキュメントの一意識別子
            file_path (str): ファイルの保存パス
            user_id (str): アップローダーのユーザーID
            request (UploadDocumentRequest): アップロードリクエストパラメータ

        Returns:
            str: パースされたドキュメントの全文

        Raises:
            BaseAppError: ドキュメントのパースまたはインデックス処理に失敗した場合

        Note:
            一時ファイルは処理後に自動的に削除される
            ドキュメントは2000文字ずつのチャンクに分割されてインデックスされる
        """
        temp_file_path = None
        try:
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=FilePath(filename).suffix
            ) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            # ファイル拡張子に応じたプロセッサを取得
            file_extension = FilePath(filename).suffix.lower()
            processor = get_processor(file_extension)

            # プロセッサでファイルを処理（LangChainのDocumentリストを取得）
            documents = processor.process(temp_file_path, filename)


            # ドキュメント全体のコンテンツを結合
            full_content = "\n\n".join([doc.page_content for doc in documents])

            excel_extensions = {".xlsx", ".xls", ".xlsm"}

            if file_extension in excel_extensions:
                # Excelの場合：
                # ExcelProcessorがすでに「1行＝1Document(チャンク)」として完璧に分割しているため、
                # 強制的な文字数分割（スプリッター）は行わず、そのまま chunks として利用する
                chunks = documents
            else:
                # チャンク分割
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=2000,
                    chunk_overlap=200,
                    separators=["。", "！", "？", "\n\n", "\n", " ", ""],
                    length_function=len,
                )
                chunks = text_splitter.split_documents(documents)

            # 各チャンクに対してMeilisearchChunkを作成
            meili_pages = []
            for chunk_num, chunk in enumerate(chunks):
                resolved_file_type = (
                    mimetypes.guess_type(filename)[0] or "application/octet-stream"
                )
                meili_page = MeilisearchChunk(
                    id=f"{document_id}_c{chunk_num}",
                    doc_id=str(document_id),
                    title=filename,
                    total_pages=chunk.metadata.get("total_pages", 1),
                    page_num=chunk.metadata.get("page_num", 1),
                    chunk_num=chunk_num + 1,
                    contents=chunk.page_content,
                    subject=request.subject,
                    path=file_path,
                    uploader=user_id,
                    file_type=resolved_file_type,
                    genre=request.genre,
                    release=request.release,
                )
                meili_pages.append(meili_page.model_dump())

            # 全チャンクを一括でMeilisearchに登録
            if meili_pages:
                await self.repository.meili_client.index("qines-gai").add_documents(
                    meili_pages
                )
                logger.info(
                    f"Successfully indexed {len(meili_pages)} chunks for document: {filename}"
                )

            return full_content

        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}, file: {filename}")
            raise BaseAppError("Failed to index document")
        finally:
            # 一時ファイルの削除
            if temp_file_path:
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(
                        f"Failed to remove temporary file: {temp_file_path}, error: {str(e)}"
                    )

    async def _delete_from_storage(
        self, document, user_id: str, s3_client: S3Client
    ) -> None:
        """S3からファイルを削除する。

        Args:
            document: 削除対象のドキュメントレコード
            user_id (str): ファイル所有者のユーザーID
            s3_client (S3Client): S3クライアント

        Note:
            ストレージ削除に失敗しても例外を発生させず、ログのみ出力する
        """
        bucket_name = os.getenv("S3_BUCKET_NAME")
        s3_key = f"{user_id}/{document.document_id}/{document.file_name}"

        try:
            s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
            waiter = s3_client.get_waiter("object_not_exists")
            waiter.wait(Bucket=bucket_name, Key=s3_key)
        except Exception as e:
            logger.error(f"Failed to delete file from storage: {str(e)}")

    async def _cleanup_resources(
        self,
        s3_client: S3Client,
        bucket_name: str,
        s3_path: str,
        document_id: uuid.UUID,
    ) -> None:
        """アップロード失敗時に部分的に作成されたリソースをクリーンアップする。

        Args:
            s3_client (S3Client): S3クライアント
            bucket_name (str): S3バケット名
            s3_path (str): S3内のファイルパス
            document_id (uuid.UUID): ドキュメントの一意識別子

        Note:
            ストレージとMeilSearchの両方からデータを削除しようとする
            各クリーンアップ処理は失敗しても例外を発生させない
        """
        # S3ファイルの削除
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=s3_path)
            logger.info("Storage cleanup successful")
        except Exception as e:
            logger.error(f"Storage cleanup failed: {str(e)}")

        # Meilisearchからのドキュメント削除
        try:
            await self.repository.meili_client.index("qines-gai").delete_document(
                str(document_id)
            )
            logger.info("Meilisearch cleanup successful")
        except Exception as e:
            logger.error(f"Meilisearch cleanup failed: {str(e)}")
