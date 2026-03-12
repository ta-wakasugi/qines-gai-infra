"""MCP Client Setup

このモジュールは、MCPサーバーと連携してツールを取得し、
LangChainエージェントで使用できるようにします。

主要な機能:
    - create_mcp_client(): src/qines_gai_backend/modules/ai/mcp.json からMultiServerMCPClientを作成
    - get_mcp_tools(): 全てのenabled=trueサーバーからツールを取得

処理フロー:
    1. src/qines_gai_backend/modules/ai/mcp.json の読み込み
    2. 環境変数展開（${VAR_NAME} と ${env:VAR_NAME} 形式に対応）
    3. Pydanticバリデーション
    4. enabled=true のサーバーのみ抽出
    5. MultiServerMCPClient 作成
"""

import json
import os
import re
from pathlib import Path
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from qines_gai_backend.logger_config import get_logger, log_function_start_end

logger = get_logger(__name__)

__all__ = ["create_mcp_client", "get_mcp_tools", "get_mcp_resources"]


# ============================================================================
# Environment Variable Expansion
# ============================================================================


@log_function_start_end
def expand_env_vars(value: Any) -> Any:
    """環境変数を展開する

    対応形式:
    - ${VAR_NAME} 形式
    - ${env:VAR_NAME} 形式（VSCode標準）

    Args:
        value: 環境変数を含む可能性のある値（文字列、辞書、リストなど）

    Returns:
        環境変数が展開された値

    Examples:
        >>> os.environ["API_KEY"] = "secret123"
        >>> expand_env_vars("Bearer ${API_KEY}")
        'Bearer secret123'
        >>> expand_env_vars("Bearer ${env:API_KEY}")
        'Bearer secret123'
    """
    if isinstance(value, str):
        # ${VAR_NAME} 形式と ${env:VAR_NAME} 形式の両方に対応
        # env: プレフィックスはオプショナル
        pattern = r"\$\{(?:env:)?([^}]+)\}"

        def replacer(match):
            var_name = match.group(1)
            env_value = os.getenv(var_name)
            if env_value is None:
                logger.warning(
                    f"環境変数 {var_name} が設定されていません。空文字列で置換します。"
                )
                return ""
            return env_value

        return re.sub(pattern, replacer, value)
    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [expand_env_vars(item) for item in value]
    else:
        return value


# ============================================================================
# MCP Client Factory
# ============================================================================


@log_function_start_end
def create_mcp_client(
    config_path: Path | str,
) -> MultiServerMCPClient:
    """
    MCP設定ファイルから MultiServerMCPClient を作成

    処理フロー:
    1. 設定ファイルの存在確認
    2. JSON読み込み
    3. 環境変数展開（${VAR_NAME} と ${env:VAR_NAME} 形式に対応）
    4. enabled=true のサーバーのみ抽出
    5. MultiServerMCPClient 生成

    Args:
        config_path: 設定ファイルのパス

    Returns:
        MultiServerMCPClient インスタンス

    Raises:
        FileNotFoundError: 設定ファイルが見つからない

    Examples:
        >>> # src/qines_gai_backend/modules/ai/mcp.json:
        >>> # {
        >>> #   "servers": {
        >>> #     "my-server": {
        >>> #       "type": "http",
        >>> #       "url": "${env:MCP_SERVER_URL}",
        >>> #       "headers": {"Authorization": "Bearer ${env:API_KEY}"},
        >>> #       "enabled": true
        >>> #     }
        >>> #   }
        >>> # }
        >>> config_path = Path(__file__).parent / "mcp.json"
        >>> client = create_mcp_client(config_path)
    """
    config_path = Path(config_path)

    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # 1. JSONファイルを読み込み
    with open(config_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    logger.debug(f"Loaded MCP config file: {config_path}")

    # 2. 環境変数を展開
    expanded_data = expand_env_vars(raw_data)
    logger.debug("Expanded environment variables in config.")

    # 3. enabled=true のサーバーのみ抽出
    servers = expanded_data.get("servers", {})
    server_configs = {}
    enabled_count = 0

    for name, server_config in servers.items():
        # enabled=false のサーバーはスキップ（デフォルトはtrue）
        if not server_config.get("enabled", True):
            logger.debug(f"MCPサーバー '{name}' は無効化されています（enabled=false）")
            continue

        # enabled フィールドを削除してそのまま渡す
        config_copy = server_config.copy()
        config_copy.pop("enabled", None)

        server_configs[name] = config_copy
        enabled_count += 1
        logger.debug(f"MCPサーバー '{name}' を有効化しました")

    logger.info(f"有効なMCPサーバー数: {enabled_count}")

    if not server_configs:
        logger.warning(
            "有効なMCPサーバーが設定ファイルにありません。空のクライアントを作成します。"
        )

    # 4. MultiServerMCPClient を作成
    logger.debug("MultiServerMCPClientインスタンスを生成します...")
    return MultiServerMCPClient(server_configs)


# ============================================================================
# Public API
# ============================================================================


@log_function_start_end
async def get_mcp_tools(client: MultiServerMCPClient) -> list[BaseTool]:
    """MCPクライアントからツールを取得

    Args:
        client: MultiServerMCPClient インスタンス

    Returns:
        list[BaseTool]: 全サーバーから取得したLangChainツールのリスト

    Example:
        >>> config_path = Path(__file__).parent / "mcp.json"
        >>> client = create_mcp_client(config_path)
        >>> mcp_tools = await get_mcp_tools(client)
        >>> tools = [get_artifact, create_artifact] + mcp_tools
    """
    try:
        # 全サーバーからツールを取得
        tools = await client.get_tools()
        logger.info(f"合計 {len(tools)} 個のMCPツールを取得しました")
        return tools

    except Exception as e:
        logger.exception(f"MCPツールの取得中に予期しないエラー: {e}")
        # エラーが発生しても空リストを返す（エージェントは動作可能）
        return []


@log_function_start_end
async def get_mcp_resources(client: MultiServerMCPClient) -> list[Any]:
    """MCPクライアントからリソースを取得

    リソースは使い方ガイド、プロンプトテンプレート、設定情報などを含みます。
    サーバー単位でエラーが発生しても、他のサーバーからの取得を継続します。

    Args:
        client: MultiServerMCPClient インスタンス

    Returns:
        list[Any]: 全サーバーから取得したリソースのリスト
            各リソースオブジェクトは以下のプロパティを持ちます:
            - metadata: dict (uri, name, description など)
            - as_string(): リソース内容を文字列として取得するメソッド

    Example:
        >>> config_path = Path(__file__).parent / "mcp.json"
        >>> client = create_mcp_client(config_path)
        >>> resources = await get_mcp_resources(client)
        >>> for resource in resources:
        >>>     uri = resource.metadata.get("uri", "")
        >>>     if "guide" in uri:
        >>>         content = resource.as_string()
        >>>         print(content)
    """
    try:
        # 全サーバーからリソースを取得
        all_resources = []
        server_names = (
            list(client.connections.keys()) if hasattr(client, "connections") else []
        )

        for server_name in server_names:
            try:
                resources = await client.get_resources(server_name)
                all_resources.extend(resources)
                logger.debug(
                    f"MCPサーバー '{server_name}' から {len(resources)} 個のリソースを取得しました"
                )
            except Exception as e:
                logger.warning(
                    f"MCPサーバー '{server_name}' からリソース取得に失敗: {e}. スキップします。"
                )
                continue

        logger.info(f"合計 {len(all_resources)} 個のMCPリソースを取得しました")
        return all_resources

    except Exception as e:
        logger.error(f"MCPリソースの取得中に予期しないエラー: {e}")
        # エラーが発生しても空リストを返す
        return []
