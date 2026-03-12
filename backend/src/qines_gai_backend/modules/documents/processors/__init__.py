"""ドキュメントプロセッサモジュール

ファイル形式ごとのドキュメント処理を提供します。
"""

from qines_gai_backend.modules.documents.processors.factory import get_processor

__all__ = ["get_processor"]
