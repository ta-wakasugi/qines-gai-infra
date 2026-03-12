from typing import Any, Type

from qines_gai_backend.config.external_resources.base import ExternalResource
from qines_gai_backend.config.external_resources.meilisearch import (
    MeilisearchConnection,
)
from qines_gai_backend.config.external_resources.postgresql import PostgreSQLConnection
from qines_gai_backend.logger_config import get_logger

logger = get_logger(__file__)


class ConnectionManager:
    """外部リソース接続の依存関係を管理するクラス。

    このクラスは外部リソースへの接続を一元管理し、アプリケーション全体で一貫した
    接続インタンスを提供します。

    各接続はプロパティとしてていきょうされ、最初のアクセス時に遅延初期化されます。

    Attributes:
        _resource_classes: このクラスで管理する外部リソースの名前とクラスオブジェクトの辞書
        _connections: 外部リソース接続インスタンス。
    """

    def __init__(self):
        """ConnectionManagerを初期化します。"""
        self._resource_classes: dict[str, Type[ExternalResource]] = {
            "meilisearch": MeilisearchConnection,
            "postgresql": PostgreSQLConnection,
        }

        self._connections: dict[str, ExternalResource | None] = {
            r: None for r in self._resource_classes.keys()
        }

    async def connect(self, resource: str) -> None:
        """特定のリソースへの接続を確立します。

        Raises:
            ValueError: 指定された`resource`が存在しないとき
        """
        if resource not in self._resource_classes.keys():
            raise ValueError(f"存在しない外部リソースです。: {resource}")

        if self._connections[resource]:
            await self._connections[resource].connect()
        else:
            resource_class = self._resource_classes[resource]
            resource_instance = resource_class()
            await resource_instance.connect()
            self._connections[resource] = resource_instance

    async def connect_all(self) -> None:
        """アプリケーションで使用する全ての外部リソースへの接続を確立します。

        このメソッドはアプリケーションの起動時に呼び出される必要があります。
        すべての外部リソースへの接続を順次確立します。
        いずれかのリソースへの接続が失敗した場合、それまで確立した接続をすべて切断してから
        エラーを発生させます。

        Raises:
            Exception: いずれかのリソースへの接続が失敗した場合。この場合、
                    すでに確立された接続はすべて切断されます。
        """
        try:
            for resource in self._resource_classes.keys():
                await self.connect(resource)
        except Exception as e:
            for resource in self._connections.values():
                if resource:
                    try:
                        await resource.disconnect()
                    except Exception:
                        logger.error(
                            f"connect_allのクリーンアップ中に"
                            f"{resource.__class__.__name__}との接続の切断に失敗しました。"
                        )
            raise RuntimeError(
                f"すべてのリソースと接続確立に失敗しました: {str(e)}"
            ) from e

    async def disconnect_all(self) -> None:
        """アプリケーションで使用している全ての外部リソースとの接続を切断します。

        このメソッドはアプリケーションの終了時に呼び出される必要があります。
        一つのリソースの切断に失敗しても、他のリソースの切断を続行します。
        すべての切断処理が終わった後、エラーが発生していた場合はまとめて報告します。

        Notes:
            シャットダウン時に呼び出されるため、できるだけ多くのリソースを
            切断するように設計されています。

        Raises:
            RuntimeError: 一つ以上のリソースの切断に失敗した場合。
                        ただし、この例外は全てのリソースの切断を試行した後に発生します。
        """
        errors = []

        for resource in self._connections.values():
            if resource:
                try:
                    await resource.disconnect()
                except Exception as e:
                    resource_name = resource.__class__.__name__
                    error_msg = f"{resource_name}との接続の切断に失敗しました: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        if errors:
            raise RuntimeError(
                "いくつかのリソースのクリーンアップに失敗しました:\n"
                + "\n".join(errors)
            )

    def get_connection(self, resource: str) -> Any:
        """特定のリソースへの接続を取得します。

        Raises:
            ValueError: 指定された`resource`が存在しないとき
        """
        if resource not in self._resource_classes.keys():
            raise ValueError(f"存在しない外部リソースです。: {resource}")

        return self._connections[resource]
