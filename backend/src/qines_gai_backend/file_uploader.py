import argparse
import asyncio
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import boto3
import pdfplumber
from botocore.exceptions import BotoCoreError, ClientError
from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.task import TaskResult
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from tqdm.asyncio import tqdm
from typing_extensions import Any

from qines_gai_backend.logger_config import get_logger
from qines_gai_backend.modules.documents.models import MeilisearchChunk
from qines_gai_backend.schemas.schema import T_Document

logger = get_logger(__file__)


@dataclass
class UploadTask:
    task_uid: str
    s3_key: str
    batch_number: int
    total_batches: int


class AutosarPdfProcessor:
    GENRE_LIST = [
        "EXP",
        "MMOD",
        "MOD",
        "PRS",
        "RS",
        "SRS",
        "SWS",
        "TPS",
        "TR",
    ]

    def __init__(
        self,
        pdf_dir: str,
        s3_bucket: str,
        concurrency: int,
        batch_size: int,
        use_local: bool = True,
    ):
        """AUTOSARの仕様書をアプリへ配置するクラス

        Args:
            pdf_dir: AUTOSARの仕様書が含まれるディレクトリ。このディレクトリ直下のPDFのみ処理する。
            s3_bucket: AWS S3のバケット名
            batch_size: 同時に処理するページの数。
            use_local: データの配置先。`True`の場合は、dockerで構築されたサービス群へデータを配置する。
                       そうでない場合は、環境変数で指定されたS3やMeilisearch、PostgreSQLへデータを配置する。
                       TODO: `False`の場合は未実装
        """
        self._pdf_dir = Path(pdf_dir)
        self._s3_bucket = s3_bucket
        self._semaphore = asyncio.Semaphore(concurrency)
        self._batch_size = batch_size
        self._use_local = use_local

        if use_local:
            endpoint_url = os.getenv("S3_ENDPOINT_URL", "http://seaweedfs:8333")
            self._s3 = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "admin"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "admin123"),
            )
            self._meili_client = AsyncClient(url="http://meilisearch:7700")
            self._pdf_index = self._meili_client.index("qines-gai")
            self._db_engine = create_async_engine(
                "postgresql+asyncpg://qinesgai:qinesgai@db:5432/qinesgai"
            )
            self._async_session = sessionmaker(
                self._db_engine, class_=AsyncSession, expire_on_commit=False
            )
            self._pending_task: dict[str, list[UploadTask]] = {}
        else:
            raise ValueError("`use_local`オプションがFalseの場合は未実装です。")

    async def _upload_to_s3(self, pdf_path: Path) -> str:
        """PDFをS3へアップロードする

        Args:
            pdf_path: アップロード対象のPDFのパス。このパスの形式は`{任意のパス}/リリースバージョン/ファイル名`となっている
                      ことを想定する。
                      例: /documents/R22-11/AUTOSAR_SWS_CANDrivder.pdf

        Returns:
            アップロードしたファイルのS3におけるキー
        """
        try:
            path_with_release = Path(*pdf_path.parts[-2:])
            s3_key = str("AUTOSAR" / path_with_release)
            await asyncio.to_thread(
                self._s3.upload_file,
                Filename=str(pdf_path),
                Bucket=self._s3_bucket,
                Key=str(s3_key),
            )
            return s3_key
        except (BotoCoreError, ClientError) as e:
            logger.error(f"S3 upload failed for {pdf_path.name}: {str(e)}")
            return None

    async def _upload_to_meilisearch(
        self,
        docs: list[MeilisearchChunk],
        s3_key: str,
        batch_number: int,
        total_batches: int,
    ) -> UploadTask | None:
        """MeilisearchへPDFの内容をアップロードする

        Args:
            docs: PDFをパースして得られた内容
            s3_key: ファイルの実態がアップロードされているS3のKey
            batch_number: 総バッチ数において、この処理が担当するバッチ数
            total_batches: 総バッチ数
        """
        try:
            if docs:
                task = await self._pdf_index.add_documents(docs)
                return UploadTask(
                    task_uid=task.task_uid,
                    s3_key=s3_key,
                    batch_number=batch_number,
                    total_batches=total_batches,
                )
        except Exception as e:
            logger.error(f"Meilisearch uplaod failed for {s3_key}: {str(e)}")
            return None

    async def _wait_for_meilisearch_task(self, task: UploadTask) -> bool:
        try:
            response = await self._meili_client.wait_for_task(
                task.task_uid,
                timeout_in_ms=None,
            )
            if response.status == "succeeded":
                duration = response.duration or "unkown"
                logger.debug(
                    f"Batch {task.batch_number}/{task.total_batches} completed in for {task.s3_key}\n"
                    f"-> Duration: {duration}, Started: {response.started_at}, Finished: {response.finished_at}"
                )
                return True
            else:
                error_details = response.error or {}
                error_type = error_details.get("typ", "unknown")
                error_message = error_details.get("message", "No error message")
                error_code = error_details.get("code", "unknown")

                err_msg = (
                    f"Task {task.task_uid} failed:\n"
                    f"-> Status: {response.status}\n"
                    f"-> Error Type: {error_type}\n"
                    f"-> Error Code: {error_code}\n"
                    f"-> Message: {error_message}\n"
                )
                if response.details:
                    err_msg += f"-> Additional Details: {response.details}"

                logger.error(err_msg)
                return False
        except Exception as e:
            logger.error(f"Meilisearch task failed: {str(e)}")
            return False

    async def _wait_for_all_tasks(self, s3_key: str) -> bool:
        """Meilisearchへのドキュメント追加タスクの完了を待つ"""
        if s3_key not in self._pending_task:
            return True

        tasks = self._pending_task[s3_key]
        results = await asyncio.gather(
            *[self._wait_for_meilisearch_task(task) for task in tasks]
        )

        succeeded = all(results)
        if succeeded:
            del self._pending_task[s3_key]

        return succeeded

    async def _save_to_db(self, pdf_path: Path, pdf_metadata: dict[str, Any]) -> bool:
        """DBへデータを保存する"""
        try:
            async with self._async_session() as session:
                pdf_record = T_Document(
                    document_id=pdf_metadata["doc_id"],
                    file_name=pdf_metadata["title"],
                    file_path=pdf_metadata["path"],
                    file_type=pdf_metadata["file_type"],
                    file_size=pdf_path.stat().st_size,
                    user_id="admin",
                    metadata_info={
                        "subject": pdf_metadata["subject"],
                        "genre": pdf_metadata["genre"],
                        "release": pdf_metadata["release"],
                    },
                )
                session.add(pdf_record)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"DB save failed for {pdf_path.name}: {str(e)}")
            return False

    async def _cleanup_failed_processing(self, s3_key: str):
        """DBへの保存が失敗したときに、配置済みのデータを削除する"""
        logger.info("Clean up data...")
        try:
            await asyncio.to_thread(
                self._s3.delete_object, Bucket=self._s3_bucket, Key=s3_key
            )
        except Exception as e:
            logger.error(f"Failed to delete {s3_key} from S3: {str(e)}")

        try:
            await self._pdf_index.delete_documents_by_filter(f"file_path = '{s3_key}'")
        except Exception as e:
            logger.error(f"Failed to delete documents from Meilisearch: {str(e)}")
        logger.info("Done!")

    async def process_pdf(self, pdf_path: Path) -> bool:
        s3_key = None
        try:
            s3_key = await self._upload_to_s3(pdf_path)
            if not s3_key:
                raise Exception("S3 upload failed")

            current_batch = []
            batch_number = 0
            total_pages = 0
            pdf_metadata = {}
            self._pending_task[s3_key] = []

            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                total_batches = (total_pages + self._batch_size - 1) // self._batch_size

                # メタデータからDBのカラム、MeilisearchのAttributeに必須の属性を取得
                # `Title`がメタデータに含まれていない場合は、ファイル名を空白区切りに変換して構成
                title = pdf.metadata.get("Title")
                if title is None or title == "":
                    title = pdf_path.stem.replace("_", " ")

                subject = pdf.metadata.get("Subject")
                if subject != "AUTOSAR":
                    subject = "others"

                # ファイル名から Web Doc Type を取得し、`genre`へ格納
                genre = None
                title_elements = pdf_path.stem.split("_")
                if "AUTOSAR" in title_elements:
                    autosar_pos = title_elements.index("AUTOSAR")
                    if len(title_elements) > autosar_pos + 1:
                        genre = title_elements[autosar_pos + 1]
                        if genre not in AutosarPdfProcessor.GENRE_LIST:
                            genre = None

                    # R23-11のようにAUTOSARの次がCP、RSなどの場合
                    if genre is None and len(title_elements) > autosar_pos + 2:
                        genre = title_elements[autosar_pos + 2]
                        if genre not in AutosarPdfProcessor.GENRE_LIST:
                            genre = None

                # MeilisearchChunkにおける、`chunk_num`, `contents` 以外はこの段階で構築
                pdf_metadata_path = f"/{self._s3_bucket}/{s3_key}"

                pdf_metadata = {
                    "doc_id": str(uuid4()),
                    "title": title,
                    "subject": subject,
                    "release": pdf_path.parent.name,
                    "genre": genre,
                    "path": pdf_metadata_path,
                    "uploader": "admin",
                    "file_type": mimetypes.guess_type(pdf_path.name)[0],
                }

                # 各ページのテキストをDocumentとして作成（ページ番号をmetadataに保持）
                docs = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        docs.append(
                            Document(
                                page_content=text,
                                metadata={"page_num": page.page_number},
                            )
                        )

                # PDFテキスト全体をチャンク分割（各チャンクにページ番号が保持される）
                char_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=2000,
                    chunk_overlap=200,
                    separators=["。", "！", "？", "\n\n", "\n", " ", ""],
                    length_function=len,
                )
                char_chunks = char_splitter.split_documents(docs)

                chunk_num = 1
                # チャンクをバッチに追加（各チャンクのmetadataからページ番号を取得）
                for chunk in char_chunks:
                    page_data = {
                        **pdf_metadata,
                        "total_pages": total_pages,
                        "page_num": chunk.metadata.get("page_num", 1),
                        "chunk_num": chunk_num,
                        "contents": chunk.page_content,
                        "id": str(uuid4()),
                    }
                    current_batch.append(page_data)
                    chunk_num += 1

                if len(current_batch) == self._batch_size:
                    batch_number += 1
                    task = await self._upload_to_meilisearch(
                        current_batch, s3_key, batch_number, total_batches
                    )
                    if task:
                        self._pending_task[s3_key].append(task)
                    current_batch = []

            if current_batch:
                batch_number += 1
                task = await self._upload_to_meilisearch(
                    current_batch, s3_key, batch_number, total_batches
                )
                if task:
                    self._pending_task[s3_key].append(task)

            # 1PDFの処理が終わるまで待機
            if not await self._wait_for_all_tasks(s3_key):
                raise Exception("Meilisearch upload failed")

            db_success = await self._save_to_db(pdf_path, pdf_metadata)
            if not db_success:
                raise Exception("DB save failed")

            return True
        except Exception as e:
            logger.error(f"Processing failed for {pdf_path.name}: {str(e)}")
            if s3_key:
                await self._cleanup_failed_processing(s3_key)
            return False

    async def process_all_pdfs(self):
        pdf_files = list(self._pdf_dir.glob("*.pdf"))

        with tqdm(total=len(pdf_files), desc="Processing PDFs") as pbar:

            async def process_with_semaphore(pdf_path):
                async with self._semaphore:
                    success = await self.process_pdf(pdf_path)
                    pbar.update(1)
                    pbar.set_postfix({"status": "success" if success else "failed"})

            tasks = [process_with_semaphore(pdf_path) for pdf_path in pdf_files]
            await asyncio.gather(*tasks)


async def create_index(meili_client: AsyncClient, index_uid: str) -> TaskResult:
    index = await meili_client.create_index(index_uid, "id")
    if index:
        settings = await index.get_settings()
        settings.filterable_attributes = [
            "page_num",
            "chunk_num",
            "release",
            "genre",
            "doc_id",
            "uploader",
        ]
        task = await index.update_settings(settings)
        result = await meili_client.wait_for_task(task.task_uid)
    return result


async def main(
    append: bool,
    target_dir: Path,
    s3_bucket: str,
    concurrency: int,
    batch_size: int,
):
    # TODO: use_localオプションを受け取り、MeilisearchのURLを変える
    meili_client = AsyncClient("http://meilisearch:7700", timeout=None)
    index = await meili_client.get_or_create_index("qines-gai")

    if not append:
        task = await index.delete()
        result = await meili_client.wait_for_task(task.task_uid)
        if result.status != "succeeded":
            logger.error("Failed to delete index")
            exit(1)

        result = await create_index(meili_client, "qines-gai")
        if result.status != "succeeded":
            logger.error("Failed to create Meilisearch index")
            exit(1)

    processor = AutosarPdfProcessor(
        target_dir, s3_bucket, concurrency, batch_size
    )
    await processor.process_all_pdfs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="QINeS GAI用のデータデプロイスクリプト"
    )
    parser.add_argument(
        "--target_dir",
        help="PDFファイルを含んだディレクトリ",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--append",
        help="インデックスに新たなドキュメントを追加する。このオプションがない場合は、インデックスをリセットして新規作成する。",
        action="store_true",
    )
    parser.add_argument(
        "--s3_bucket",
        help="PDFをアップロードするS3のバケット（デフォルトは'qines-gai-local'）",
        default="qines-gai-local",
        type=str,
    )
    parser.add_argument(
        "--concurrency",
        help="平行に処理するファイル数（デフォルトは４）",
        default=4,
        type=int,
    )
    parser.add_argument(
        "--batch_size",
        help="Meilisearchへ一度に追加するPDFのページ数（デフォルトは500）",
        default=500,
        type=int,
    )
    # TODO: ここにuse_localのオプションを追加

    args = parser.parse_args()

    target_dir = Path(args.target_dir)
    if not target_dir.is_dir():
        raise ValueError("引数`target_dir`にはディレクトリを指定してください")

    asyncio.run(
        main(
            args.append,
            target_dir,
            args.s3_bucket,
            args.concurrency,
            args.batch_size,
        )
    )
