import os

from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.errors import MeilisearchError
from meilisearch_python_sdk.models.task import TaskResult

from qines_gai_backend.config.external_resources.base import ExternalResource


class MeilisearchConnection(ExternalResource[AsyncClient]):
    """Meilisearchへの接続を管理するクラス。

    このクラスはMeilisearchへの接続を管理し、
    meilisearch-python-asyncを用いた非同期アクセスを提供します。

    接続設定は環境変数から読み込まれます：
        - MEILISEARCH_HOST: Meilisearchサーバーのホスト名またはIPアドレス
        - MEILISEARCH_API_KEY: MeilisearchのAPIキー (マスターキー推奨)

    Attributes:
        _client: Meilisearchの非同期クライアントインスタンス。
    """

    def __init__(self):
        """MeilisearchConnectionを初期化します。"""
        self._client: AsyncClient | None = None

    async def connect(self) -> None:
        """Meilisearchへの接続を確立します。

        環境変数から接続情報を読み込み、Meilisearchへの接続を確立します。
        接続後、必要なインデックスが存在しない場合は自動的に作成します。
        """
        if not self._client:
            host = os.getenv("MEILISEARCH_HOST")
            api_key = os.getenv("MEILISEARCH_API_KEY")

            if not host:  # or not api_key:
                raise RuntimeError(
                    "Meilisearchへの接続情報が設定されていません。"
                    "MEILISEARCH_HOSTを設定してください。"
                    # "MEILISEARCH_HOSTとMEILISEARCH_API_KEYを設定してください。"
                )

            self._client = AsyncClient(host, api_key)

            try:  # 接続確認
                await self._client.health()
                # インデックスの初期化
                await self._ensure_index_exists()
            except MeilisearchError as e:
                self._client = None  # 接続失敗時はclientをNoneに戻す
                raise RuntimeError(f"Meilisearchへの接続に失敗しました: {e}") from e

    async def disconnect(self):
        """Meilisearchとの接続を切断します。

        既存の接続をクローズします。
        """
        if self._client:
            await self._client.aclose()
            self._client = None

    def get_client(self) -> AsyncClient:
        """Meilisearchクライアントを取得します。

        Returns:
            AsyncClient: Meilisearchの非同期クライアント。

        Raises:
            RuntimeError: 接続が初期化されていない場合。
        """
        if not self._client:
            raise RuntimeError("Meilisearchへの接続が初期化されていません。")
        return self._client

    async def _ensure_index_exists(self) -> None:
        """必要なインデックスが存在することを確認し、存在しない場合は作成します。

        file_uploader.pyのcreate_index関数と同じ設定でインデックスを作成します。
        """
        if not self._client:
            return

        index_uid = "qines-gai"

        try:
            # インデックスが既に存在するかチェック
            await self._client.get_index(index_uid)
        except MeilisearchError:
            # インデックスが存在しない場合、新規作成
            await self._create_index(index_uid)

    async def _create_index(self, index_uid: str) -> TaskResult:
        """新しいインデックスを作成し、必要な設定を適用します。

        Args:
            index_uid: 作成するインデックスのUID

        Returns:
            TaskResult: インデックス作成・設定更新のタスク結果
        """
        if not self._client:
            raise RuntimeError("Meilisearchクライアントが初期化されていません。")

        index = await self._client.create_index(index_uid, "id")
        if index:
            settings = await index.get_settings()
            settings.filterable_attributes = [
                "page_num",
                "chunk_num",
                "release",
                "genre",
                "doc_id",
                "uploader",
                "file_path",
            ]
                
            task = await index.update_settings(settings)
            result = await self._client.wait_for_task(task.task_uid)
            return result

        raise RuntimeError(f"インデックス '{index_uid}' の作成に失敗しました。")
