from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class ExternalResource(ABC, Generic[T]):
    """外部リソース接続の抽象基底クラス。

    このクラスはシングルトンパターンを実装し、外部リソース接続（データベースや検索エンジン）のインターフェースを定義します。
    すべての具象接続クラスはこのクラスを継承し、抽象メソッドを実装する必要があります。

    シングルトンパターンにより、アプリケーションのライフサイクルを通じて
    各接続タイプのインスタンスが１つだけ存在することが保証されます。

    Attributes:
        _instance: シングルトンインスタンスを保持するクラス変数。

    Type Parameters:
        T: 接続オブジェクトの型。例えば、AsyncSession、Clientなど。
    """

    _instance = None

    def __new__(cls):
        """クラスのインスタンスが存在しない場合、新しいインスタンスを作成します

        シングルトンパターンを実装し、クラスのインスタンスが１つだけ存在することを保証します。
        インスタンスがすでに存在する場合は、そのインスタンスを返します。

        Returns:
            ExternalResource: クラスのシングルトンインスタンス。
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @abstractmethod
    async def connect(self) -> None:
        """外部リソースへの接続を確立します

        このメソッドは接続の初期化時に呼び出される必要があります。
        接続プールの作成、クライアントの初期化など、必要なセットアップを全て処理する必要があります。

        Raises:
            RuntimeError: 接続を確立できない場合。
            Exception: リソース固有の接続エラーが発生した場合。
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """外部リソースとの接続を切断します。

        このメソッドはアプリケーションのシャットダウン時に呼び出される必要があります。
        すべての接続を適切に閉じ、リソースをクリーンアップし、必要な終了処理を実行する必要があります。

        Raises:
            RuntimeError: 接続を正しく閉じることができない場合。
            Exception: リソース固有の切断エラーが発生した場合。
        """
        pass
