"""Update module business logic layer

成果物の更新処理に関するビジネスロジックを提供します。
AIによって生成された成果物をドキュメントとして登録・更新し、
既存ドキュメントとの置き換えや関連コレクションの更新を行います。

主な機能:
- 成果物からドキュメントへの変換・登録
- 既存ドキュメントの検索・削除・置き換え
- MeilSearchインデックスの更新
- S3への成果物保存
- コレクション内のドキュメント参照更新
- エラー時のロールバック処理
"""

import os
import uuid
from io import BytesIO
from typing import Any, Dict, Optional

from mypy_boto3_s3 import S3Client

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.artifacts.repositories import ArtifactRepository
from qines_gai_backend.modules.conversion.repositories import ConversionRepository
from qines_gai_backend.modules.documents.models import MeilisearchChunk
from qines_gai_backend.modules.documents.repositories import DocumentRepository
from qines_gai_backend.shared.exceptions import (
    ArtifactNotFoundError,
    DocumentNotFoundError,
    DocumentUpdateError,
)

logger = get_logger(__name__)


class ConversionService:
    """成果物更新関連のビジネスロジック層。

    AIによって生成された成果物をドキュメントとして更新・登録する処理を担当します。
    主な責任範囲:
    - 成果物情報の取得と検証
    - 既存ドキュメントの検索と管理
    - ドキュメントの作成・更新・削除
    - MeilSearchインデックスの更新
    - S3へのファイル保存
    - コレクション内参照の更新
    - エラー時のロールバック処理

    トランザクション管理:
    すべての操作はトランザクション内で実行され、
    エラー発生時には自動的にロールバックされます。
    """

    def __init__(
        self,
        repository: ConversionRepository,
        document_repo: DocumentRepository,
        artifact_repo: ArtifactRepository,
    ) -> None:
        """ConversionServiceを初期化する。

        Args:
            repository (UpdateRepository): 成果物・ドキュメント関連のデータアクセスレポジトリ
        """
        self.repository = repository
        self.document_repo = document_repo
        self.artifact_repo = artifact_repo
        self._logger = logger

    @log_function_start_end
    async def update_document_from_artifact(
        self,
        public_collection_id: str,
        artifact_id: uuid.UUID,
        version: int,
        user_id: str,
        s3_client: S3Client,
    ) -> Dict[str, Any]:
        """成果物をもとにドキュメントを上書き保存する。

        指定された成果物をドキュメントとして登録・更新します。
        既存の同名ドキュメントがある場合は置き換え、
        コレクション内の参照も更新します。

        処理フロー:
        1. artifact_idで既存ドキュメントを検索
        2. 既存ドキュメントがある場合:
           - MeilSearchから削除
           - データベースから削除
        3. S3に成果物を保存
        4. 新しいドキュメントとして登録（DB + MeilSearch）
        5. コレクションドキュメントの参照を更新
        6. トランザクションをコミット

        エラー時のロールバック:
        処理中にエラーが発生した場合、すべての変更を自動的にロールバックし、
        既存データの復元を試みます。

        Args:
            public_collection_id (str): コレクションの公開コレクションID
            artifact_id (uuid.UUID): 成果物の一意識別子
            version (int): 成果物のバージョン番号（1以上）
            user_id (str): 処理を実行するユーザーのID
            s3_client (S3Client): ファイル保存用のS3クライアント

        Returns:
            Dict[str, Any]: 更新処理の結果情報
                - document_id (str): 更新後のドキュメントID
                - title (str): ドキュメントのタイトル
                - old_document_id (Optional[str]): 置き換え前のドキュメントID
                - updated_collections (int): 更新されたコレクション数

        Raises:
            ArtifactNotFoundError: 指定された成果物がデータベースに存在しない場合
            DocumentUpdateError: ドキュメントの更新処理中にエラーが発生した場合
            BaseAppError: その他のアプリケーションエラーが発生した場合
        """
        # ドキュメントID管理変数
        document_id: Optional[str] = None

        try:
            self._logger.info(
                f"Starting document update process for artifact {artifact_id} v{version}"
            )

            # 1. 成果物情報を取得
            artifact = await self.artifact_repo.get_artifact_by_id_and_version(
                artifact_id, version
            )
            if not artifact:
                raise ArtifactNotFoundError(
                    f"Artifact not found: artifact_id={artifact_id}, version={version}"
                )

            # 成果物からタイトルと内容を抽出
            title = artifact.title
            content = artifact.content

            # タイトルと内容の検証
            if not title or not title.strip():
                raise DocumentUpdateError("Artifact title is empty or invalid")
            if not content or not content.strip():
                raise DocumentUpdateError("Artifact content is empty or invalid")

            self._logger.info(
                f"Retrieved artifact: title='{title}', content_length={len(content)}"
            )

            # 2. 成果物ID（上書き追加のタイミングでは成果物ID＝ドキュメントIDになっている）で既存ドキュメントを検索
            self._logger.info(f"Searching for existing document with title: '{title}'")
            existing_document = await self.document_repo.get_document_by_id(
                str(artifact_id), user_id
            )

            # 3. 既存ドキュメントがある場合のみ既存ドキュメントを削除
            if existing_document:
                document_id = str(existing_document.document_id)
                self._logger.info(
                    f"Found existing document to replace: ID={document_id}"
                )

                # MeilSearchから既存ドキュメントを削除
                self._logger.info(
                    f"Deleting existing document from MeilSearch: {document_id}"
                )
                await self._delete_from_meilisearch(document_id)

                # データベースから既存ドキュメントを削除
                self._logger.info(
                    f"Deleting existing document from database: {document_id}"
                )
                await self.document_repo.delete_document(existing_document)
            else:
                document_id = str(artifact_id)
                self._logger.info("No existing document found - creating new document")

            # 4. S3に成果物を保存（ファイルとして保存）
            self._logger.info(f"Saving artifact to S3: {title}")
            result = {"document_id": document_id, "title": title}
            file_path = await self._save_to_s3(
                document_id, content, title, user_id, s3_client
            )

            # 5. ドキュメントIDをもとに、成果物をドキュメントとして登録
            self._logger.info("Registering artifact as new document")
            await self._register_as_document(
                document_id, title, content, user_id, file_path
            )

            # 6. コレクションにドキュメントを追加
            self._logger.info(f"Adding document to collection: {public_collection_id}")
            await self.repository.add_document_to_collection(
                public_collection_id, document_id
            )

            # 7. すべての操作が成功した場合のみトランザクションをコミット
            self._logger.info("Committing database transaction")
            await self.repository.commit()
            await self.document_repo.commit()

            # 成功結果を返却
            result = {"document_id": document_id, "title": title}

            self._logger.info(f"Document update completed successfully: {result}")
            return result

        except (ArtifactNotFoundError, DocumentNotFoundError) as e:
            # 予期されるエラーのロールバック処理
            self._logger.warning(f"Expected error during document update: {str(e)}")
            await self.repository.rollback()
            await self.document_repo.rollback()
            raise
        except DocumentUpdateError as e:
            # ドキュメント更新固有のエラーのロールバック処理
            self._logger.error(f"Document update error: {str(e)}")
            await self.repository.rollback()
            await self.document_repo.rollback()
            raise
        except Exception as e:
            # 予期しないエラーのロールバック処理
            error_msg = f"Unexpected error during document update: {str(e)}"
            self._logger.error(error_msg)
            await self.repository.rollback()
            await self.document_repo.rollback()
            raise DocumentUpdateError(error_msg) from e

    async def _delete_from_meilisearch(self, document_id: str) -> None:
        """MeilSearchからドキュメントを削除する

        Args:
            document_id (str): 削除対象のドキュメントID
        """
        try:
            index = self.repository.meili_client.index("qines-gai")
            task = await index.delete_documents_by_filter(
                filter=[f"doc_id = '{document_id}'"]
            )
            await self.repository.meili_client.wait_for_task(
                task.task_uid, raise_for_status=True
            )
        except Exception as e:
            logger.error(f"Failed to delete from MeilSearch: {str(e)}")
            raise

    async def _register_as_document(
        self, document_id: str, title: str, content: str, user_id: str, file_path: str
    ) -> None:
        """成果物をドキュメントとして登録する

        Args:
            document_id (str): ドキュメントID
            title (str): ドキュメントタイトル
            content (str): ドキュメント内容
            user_id (str): ユーザーID
            file_path (str): ファイルパス
        """

        try:
            # ドキュメントをデータベースに登録
            document = await self.document_repo.create_document(
                document_id=document_id,
                file_name=f"{title}.md",
                file_path=file_path,
                file_size=len(content.encode("utf-8")),
                content=content,
                user_id=user_id,
                subject="others",
                genre=None,
                release=None,
                file_type="text/markdown",
            )

            # MeilSearchに登録
            meili_page = MeilisearchChunk(
                id=f"{document_id}_p1",
                doc_id=document_id,
                title=title,
                total_pages=1,
                page_num=1,
                chunk_num=1,
                contents=content,
                subject="others",
                path=document.file_path,
                uploader=user_id,
                file_type="text/markdown",
                genre=None,
                release=None,
            )

            await self.repository.meili_client.index("qines-gai").add_documents(
                [meili_page.model_dump()]
            )

        except Exception as e:
            error_msg = f"Failed to register document: {str(e)}"
            self._logger.error(error_msg)
            raise DocumentUpdateError(error_msg) from e

    async def _save_to_s3(
        self,
        document_id: str,
        content: str,
        title: str,
        user_id: str,
        s3_client: S3Client,
    ) -> str:
        """成果物をS3に保存する。

        マークダウンファイルとしてS3に保存します。
        ファイルはユーザー別のディレクトリに置かれます。

        Args:
            document_id (str): 保存するドキュメントのドキュメントID
            content (str): 保存するマークダウンコンテンツ
            title (str): ファイル名のベース（.mdが追加されます）
            user_id (str): ファイルの所有者ユーザーID
            s3_client (S3Client): S3アップロード用クライアント

        Returns:
            str: ファイルの保存パス

        Raises:
            DocumentUpdateError: ファイルの保存に失敗した場合
        """
        # S3パスを構築（ユーザー別ディレクトリ + artifactsサブディレクトリ）
        bucket_name = os.getenv("S3_BUCKET_NAME")
        s3_path = f"{user_id}/{document_id}/{title}.md"

        try:
            self._logger.debug(f"Saving file to storage: {s3_path}")

            # S3にアップロード
            if not bucket_name:
                raise DocumentUpdateError(
                    "S3_BUCKET_NAME environment variable is not set"
                )

            # コンテンツをバイトストリームに変換してアップロード
            content_bytes = content.encode("utf-8")
            s3_client.upload_fileobj(
                BytesIO(content_bytes),
                bucket_name,
                s3_path,
            )

            self._logger.debug(f"File uploaded to S3: s3://{bucket_name}/{s3_path}")

            return f"/{bucket_name}/{s3_path}"

        except Exception as e:
            error_msg = f"Failed to save file to storage: {str(e)}"
            self._logger.error(error_msg)
            raise DocumentUpdateError(error_msg) from e

    @log_function_start_end
    async def add_document_from_artifact(
        self,
        public_collection_id: str,
        artifact_id: uuid.UUID,
        version: int,
        user_id: str,
        s3_client: S3Client,
    ) -> Dict[str, Any]:
        """成果物をもとにドキュメントを新規追加する。

        指定された成果物を新しいドキュメントとして登録します。
        成果物IDを新しいドキュメントIDに変更し、コレクションに追加します。

        処理フロー:
        1. 成果物情報を取得
        2. 新しいドキュメントIDを生成
        3. S3に成果物を保存
        4. 成果物を新しいドキュメントとして登録（DB + MeilSearch）
        5. コレクションにドキュメントを追加
        6. 成果物の成果物IDをドキュメントIDに変更
        7. トランザクションをコミット

        Args:
            public_collection_id (str): コレクションの公開コレクションID
            artifact_id (uuid.UUID): 成果物の一意識別子
            version (int): 成果物のバージョン番号（1以上）
            user_id (str): 処理を実行するユーザーのID
            s3_client (S3Client): ファイル保存用のS3クライアント

        Returns:
            Dict[str, Any]: 新規追加処理の結果情報
                - document_id (str): 新しいドキュメントID
                - title (str): ドキュメントのタイトル

        Raises:
            ArtifactNotFoundError: 指定された成果物がデータベースに存在しない場合
            DocumentUpdateError: ドキュメントの追加処理中にエラーが発生した場合
            BaseAppError: その他のアプリケーションエラーが発生した場合
        """
        try:
            self._logger.info(
                f"Starting document add process for artifact {artifact_id} v{version}"
            )

            # 1. 成果物情報を取得
            artifact = await self.artifact_repo.get_artifact_by_id_and_version(
                artifact_id, version
            )
            if not artifact:
                raise ArtifactNotFoundError(
                    f"Artifact not found: artifact_id={artifact_id}, version={version}"
                )

            # 成果物からタイトルと内容を抽出
            title = artifact.title
            content = artifact.content

            # タイトルと内容の検証
            if not title or not title.strip():
                raise DocumentUpdateError("Artifact title is empty or invalid")
            if not content or not content.strip():
                raise DocumentUpdateError("Artifact content is empty or invalid")

            self._logger.info(
                f"Retrieved artifact: title='{title}', content_length={len(content)}"
            )

            # 2. artifact_idをそのままdocument_idとして使用
            # これによりedit後も同じIDで更新できる
            document_id = str(artifact_id)

            # 3. S3に成果物を保存（ファイルとして保存）
            self._logger.info(f"Saving artifact to S3: {title}")
            file_path = await self._save_to_s3(
                document_id, content, title, user_id, s3_client
            )

            # 4. 成果物をドキュメントとして登録
            self._logger.info("Registering artifact as new document")
            await self._register_as_document(
                document_id, title, content, user_id, file_path
            )

            # 5. コレクションにドキュメントを追加
            self._logger.info(f"Adding document to collection: {public_collection_id}")
            await self.repository.add_document_to_collection(
                public_collection_id, document_id, add_flag=True
            )

            # 6. すべての操作が成功した場合のみトランザクションをコミット
            self._logger.info("Committing database transaction")
            await self.repository.commit()
            await self.document_repo.commit()

            # 成功結果を返却
            result = {"document_id": document_id, "title": title}

            self._logger.info(f"Document add completed successfully: {result}")
            return result

        except (ArtifactNotFoundError, DocumentNotFoundError) as e:
            # 予期されるエラーのロールバック処理
            self._logger.warning(f"Expected error during document add: {str(e)}")
            await self.repository.rollback()
            await self.document_repo.rollback()

            raise
        except DocumentUpdateError as e:
            # ドキュメント追加固有のエラーのロールバック処理
            self._logger.error(f"Document add error: {str(e)}")
            await self.repository.rollback()
            await self.document_repo.rollback()

            raise
        except Exception as e:
            # 予期しないエラーのロールバック処理
            error_msg = f"Unexpected error during document add: {str(e)}"
            self._logger.error(error_msg)
            await self.repository.rollback()
            await self.document_repo.rollback()

            raise DocumentUpdateError(error_msg) from e
