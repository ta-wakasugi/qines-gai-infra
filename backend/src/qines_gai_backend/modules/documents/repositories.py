import mimetypes
import os
from typing import Optional
from uuid import UUID

from meilisearch_python_sdk import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.ai.llm_wrapper.wrapper import LLMWrapper
from qines_gai_backend.schemas.schema import T_Document
from qines_gai_backend.shared.exceptions import (
    BaseAppError,
    DocumentNotAuthorizedError,
    DocumentNotFoundError,
)

logger = get_logger(__name__)


class DocumentRepository:
    """ドキュメント関連のデータアクセス層"""

    def __init__(self, session: AsyncSession, meili_client: AsyncClient):
        """DocumentRepositoryを初期化する。

        Args:
            session (AsyncSession): SQLAlchemyの非同期セッション
            meili_client (AsyncClient): MeilSearchの非同期クライアント
        """
        self.session = session
        self.meili_client = meili_client

    @log_function_start_end
    async def create_document(
        self,
        document_id: UUID,
        file_name: str,
        file_path: str,
        file_size: int,
        content: str,
        user_id: str,
        subject: str = "others",
        genre: Optional[str] = None,
        release: Optional[str] = None,
        is_shared: bool = False,
        file_type: Optional[str] = None,
    ) -> T_Document:
        """新しいドキュメントをデータベースに作成する。

        Args:
            document_id (UUID): ドキュメントの一意識別子
            file_name (str): ファイル名
            file_path (str): ファイルの保存パス
            file_size (int): ファイルサイズ（バイト）
            content (str): ドキュメントの内容
            user_id (str): ドキュメントの所有者ユーザーID
            subject (str, optional): ドキュメントの主題カテゴリ。デフォルトは'others'
            genre (Optional[str], optional): ドキュメントのジャンル。デフォルトはNone
            release (Optional[str], optional): リリース情報。デフォルトはNone
            is_shared (bool, optional): 共有フラグ。デフォルトはFalse
            file_type (Optional[str], optional): MIMEタイプ。指定しない場合はファイル名から推測

        Returns:
            T_Document: 作成されたドキュメントのデータベースレコード
        """
        try:
            metadata_info = {
                "subject": subject,
            }
            if genre:
                metadata_info["genre"] = genre
            if release:
                metadata_info["release"] = release

            # contentの要約生成ロジックの追加
            content_summary = None
            try:
                # LLMを使用してcontentの要約を生成
                wrapper = LLMWrapper()
                model = wrapper.get_llm(model_type=os.getenv("LLM_TYPE"), temperature=0)

                # 要約生成プロンプト
                # TODO: contentが長すぎる場合の対応（分割して要約→統合など）
                # TODO: サマリ生成中にUIもブロックされるため非同期アップロードを検討
                summarization_prompt = f"""
 あなたの役割は、与えられたドキュメントの内容を詳細に要約することです。
 ドキュメントに章立てがある場合は、章ごとに何が書かれているかを整理して記述してください。
 各章の要点、記載されている内容の概要、重要な情報や論点などを明確にまとめ、初めてそのドキュメントを見る人でも、どこに何が書かれているかが把握できるレベルの具体性を持たせてください。
 また、この要約はドキュメントの編集時の影響範囲を調査するために使用します。そのため、ドキュメント内のどの情報と関連性があるかも調査し、それらを要約に含めてください。
 要約は、章のタイトルと対応する要約、この章の内容に変更を加えた場合にドキュメント内の他の変更が生じる部分を関連性として以下のフォーマットのように記述してください。

 フォーマット：
 # 章立て
 ## 内容の要約
 - A
 - B
 ## ドキュメント内の関連性
 - Aを変更した際に2章のCに変更が及ぶ可能性があり。

 ドキュメント内容:
 {content}

 要約:"""

                # LLMで要約生成
                response = model.invoke(summarization_prompt)
                content_summary = (
                    response.content if hasattr(response, "content") else str(response)
                )

                logger.info(
                    f"Content summary generated successfully for document: {document_id}"
                )

            except Exception as e:
                logger.warning(f"Failed to generate content summary: {str(e)}")
                content_summary = "要約の生成に失敗しました"

            # file_typeが明示的に渡された場合はそれを使用、なければファイル名から推測
            resolved_file_type = (
                file_type
                or mimetypes.guess_type(file_name)[0]
                or "application/octet-stream"
            )

            document = T_Document(
                document_id=document_id,
                file_name=file_name,
                file_path=file_path,
                file_type=resolved_file_type,
                file_size=file_size,
                user_id=user_id,
                is_shared=is_shared,
                summary=content_summary,
                metadata_info=metadata_info,
            )
            self.session.add(document)
            await self.session.flush()
            return document
        except Exception:
            raise BaseAppError("Failed to save document information")

    @log_function_start_end
    async def get_document_by_id(
        self, document_id: str, user_id: Optional[str] = None
    ) -> T_Document:
        """ドキュメントIDでドキュメントを取得し、権限チェックを実行する。

        Args:
            document_id (str): 取得したいドキュメントのID（UUID文字列）
            user_id (Optional[str], optional): 権限チェック用のユーザーID。デフォルトはNone

        Returns:
            T_Document: 取得されたドキュメントのデータベースレコード

        Raises:
            DocumentNotFoundError: ドキュメントが存在しない、またはUUID形式が無効な場合
            DocumentNotAuthorizedError: ユーザーIDが指定された場合で、権限がない場合
        """
        try:
            doc_uuid = UUID(document_id)
        except ValueError:
            raise DocumentNotFoundError()

        query = select(T_Document).filter_by(document_id=doc_uuid)
        result = await self.session.execute(query)
        document = result.scalar()

        if not document:
            raise DocumentNotFoundError()

        if user_id and document.user_id != user_id:
            raise DocumentNotAuthorizedError()

        return document

    @log_function_start_end
    async def get_document_with_collections(
        self, document_id: str, user_id: Optional[str] = None
    ) -> T_Document:
        """ドキュメントとそれに関連するコレクション情報を一括取得する。

        Args:
            document_id (str): 取得したいドキュメントのID（UUID文字列）
            user_id (Optional[str], optional): 権限チェック用のユーザーID。デフォルトはNone

        Returns:
            T_Document: コレクション関連情報を含むドキュメントのデータベースレコード

        Raises:
            DocumentNotFoundError: ドキュメントが存在しない、またはUUID形式が無効な場合
            DocumentNotAuthorizedError: ユーザーIDが指定された場合で、権限がない場合

        Note:
            eager loadingを使用してコレクション関連情報を一度に取得する
        """
        try:
            doc_uuid = UUID(document_id)
        except ValueError:
            raise DocumentNotFoundError()

        query = (
            select(T_Document)
            .filter_by(document_id=doc_uuid)
            .options(selectinload(T_Document.collection_documents))
        )
        result = await self.session.execute(query)
        document = result.scalar()

        if not document:
            raise DocumentNotFoundError()

        if user_id and document.user_id != user_id:
            raise DocumentNotAuthorizedError()

        # eager loadingを確実にするため、collection_documentsアクセスを強制
        for collection_doc in document.collection_documents:
            _ = collection_doc.collection_id
            _ = collection_doc.position

        return document

    @log_function_start_end
    async def delete_document(self, document: T_Document) -> None:
        """指定されたドキュメントをデータベースから削除する。

        Args:
            document (T_Document): 削除するドキュメントのデータベースレコード

        Note:
            物理削除であり、復元はできない。関連するコレクションやメッセージにも影響する
        """
        await self.session.delete(document)
        await self.session.flush()

    async def commit(self) -> None:
        """データベーストランザクションをコミットし、変更を確定する。

        Raises:
            データベースエラーが発生した場合の例外
        """
        await self.session.commit()

    async def rollback(self) -> None:
        """データベーストランザクションをロールバックし、変更を破棄する。

        Note:
            エラー発生時や例外ハンドリングで使用される
        """
        await self.session.rollback()
