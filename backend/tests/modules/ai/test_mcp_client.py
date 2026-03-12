import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from qines_gai_backend.modules.ai.mcp_client import (
    create_mcp_client,
    expand_env_vars,
    get_mcp_resources,
    get_mcp_tools,
)


class TestExpandEnvVars:
    """環境変数展開のテスト"""

    def test_expand_env_vars_001_simple_string_dollar_brace_format(self, monkeypatch):
        """${VAR_NAME}形式の単純な文字列の環境変数展開"""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = expand_env_vars("Hello ${TEST_VAR}")
        assert result == "Hello test_value"

    def test_expand_env_vars_002_vscode_env_format(self, monkeypatch):
        """${env:VAR_NAME}形式（VSCode標準）の環境変数展開"""
        monkeypatch.setenv("API_KEY", "secret123")
        result = expand_env_vars("Bearer ${env:API_KEY}")
        assert result == "Bearer secret123"

    def test_expand_env_vars_003_dict(self, monkeypatch):
        """辞書内の環境変数展開"""
        monkeypatch.setenv("TOKEN", "secret123")
        input_dict = {
            "authorization": "Bearer ${TOKEN}",
            "content-type": "application/json",
            "nested": {"api_key": "${env:TOKEN}"},
        }
        result = expand_env_vars(input_dict)
        assert result["authorization"] == "Bearer secret123"
        assert result["content-type"] == "application/json"
        assert result["nested"]["api_key"] == "secret123"

    def test_expand_env_vars_004_list(self, monkeypatch):
        """リスト内の環境変数展開"""
        monkeypatch.setenv("PATH_VAR", "/app/docs")
        input_list = ["${PATH_VAR}", "normal_value", {"path": "${env:PATH_VAR}"}]
        result = expand_env_vars(input_list)
        assert result[0] == "/app/docs"
        assert result[1] == "normal_value"
        assert result[2]["path"] == "/app/docs"

    def test_expand_env_vars_005_undefined_var(self, monkeypatch, caplog):
        """未定義の環境変数は空文字列に展開される"""
        monkeypatch.delenv("UNDEFINED_VAR", raising=False)
        result = expand_env_vars("Hello ${UNDEFINED_VAR}")
        assert result == "Hello "
        assert "環境変数 UNDEFINED_VAR が設定されていません" in caplog.text

    def test_expand_env_vars_006_no_expansion(self):
        """環境変数を含まない値はそのまま返される"""
        assert expand_env_vars("normal string") == "normal string"
        assert expand_env_vars(123) == 123
        assert expand_env_vars(None) is None
        assert expand_env_vars(True) is True

    def test_expand_env_vars_007_complex_nested_structure(self, monkeypatch):
        """複雑にネストされた構造の環境変数展開"""
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("API_KEY", "secret123")

        input_data = {
            "database": {
                "host": "${DB_HOST}",
                "port": "${DB_PORT}",
                "connection_string": "postgresql://${DB_HOST}:${DB_PORT}/db",
            },
            "api": {"endpoints": ["https://${DB_HOST}/api"], "key": "${env:API_KEY}"},
        }

        result = expand_env_vars(input_data)

        assert result["database"]["host"] == "localhost"
        assert result["database"]["port"] == "5432"
        assert (
            result["database"]["connection_string"] == "postgresql://localhost:5432/db"
        )
        assert result["api"]["endpoints"][0] == "https://localhost/api"
        assert result["api"]["key"] == "secret123"


class TestCreateMCPClient:
    """create_mcp_client関数のテスト"""

    def test_create_mcp_client_001_basic_functionality(self, tmp_path, monkeypatch):
        """基本的な動作確認"""
        config_data = {
            "servers": {
                "test-server": {
                    "type": "http",
                    "url": "https://example.com/mcp",
                    "headers": {"Content-Type": "application/json"},
                    "enabled": True,
                }
            }
        }
        config_file = tmp_path / "mcp.json"
        config_file.write_text(json.dumps(config_data))

        # MultiServerMCPClientをモック
        with patch(
            "qines_gai_backend.modules.ai.mcp_client.MultiServerMCPClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            result = create_mcp_client(config_file)

            # MultiServerMCPClientが正しい引数で呼ばれたか確認
            mock_client.assert_called_once()
            call_args = mock_client.call_args[0][0]
            assert "test-server" in call_args
            # enabled フィールドは削除されている
            assert "enabled" not in call_args["test-server"]
            # 他のフィールドはそのまま渡される
            assert call_args["test-server"]["type"] == "http"
            assert call_args["test-server"]["url"] == "https://example.com/mcp"
            assert call_args["test-server"]["headers"] == {
                "Content-Type": "application/json"
            }

            assert result == mock_instance

    def test_create_mcp_client_002_env_expansion(self, tmp_path, monkeypatch):
        """環境変数が正しく展開される"""
        monkeypatch.setenv("MCP_SERVER_URL", "https://example.com/mcp")
        monkeypatch.setenv("API_KEY", "secret123")

        config_data = {
            "servers": {
                "test-server": {
                    "type": "http",
                    "url": "${env:MCP_SERVER_URL}",
                    "headers": {"Authorization": "Bearer ${API_KEY}"},
                    "enabled": True,
                }
            }
        }
        config_file = tmp_path / "mcp.json"
        config_file.write_text(json.dumps(config_data))

        with patch(
            "qines_gai_backend.modules.ai.mcp_client.MultiServerMCPClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            create_mcp_client(config_file)

            call_args = mock_client.call_args[0][0]
            assert call_args["test-server"]["type"] == "http"
            assert call_args["test-server"]["url"] == "https://example.com/mcp"
            assert (
                call_args["test-server"]["headers"]["Authorization"]
                == "Bearer secret123"
            )
            assert "enabled" not in call_args["test-server"]

    def test_create_mcp_client_003_enabled_only(self, tmp_path):
        """enabled=trueのサーバーのみが含まれる"""
        config_data = {
            "servers": {
                "enabled-server": {
                    "type": "http",
                    "url": "https://enabled.com/mcp",
                    "enabled": True,
                },
                "disabled-server": {
                    "type": "http",
                    "url": "https://disabled.com/mcp",
                    "enabled": False,
                },
            }
        }
        config_file = tmp_path / "mcp.json"
        config_file.write_text(json.dumps(config_data))

        with patch(
            "qines_gai_backend.modules.ai.mcp_client.MultiServerMCPClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            create_mcp_client(config_file)

            call_args = mock_client.call_args[0][0]
            assert len(call_args) == 1
            assert "enabled-server" in call_args
            assert "disabled-server" not in call_args

    def test_create_mcp_client_004_file_not_found(self, tmp_path):
        """設定ファイルが存在しない場合はFileNotFoundError"""
        non_existent_file = tmp_path / "non_existent.json"

        with pytest.raises(FileNotFoundError) as exc_info:
            create_mcp_client(non_existent_file)

        assert "Config file not found" in str(exc_info.value)

    def test_create_mcp_client_005_invalid_json(self, tmp_path):
        """不正なJSONの場合はJSONDecodeError"""
        config_file = tmp_path / "mcp.json"
        config_file.write_text("{ invalid json")

        with pytest.raises(json.JSONDecodeError):
            create_mcp_client(config_file)

    def test_create_mcp_client_006_no_enabled_servers(self, tmp_path, caplog):
        """有効なサーバーがない場合は警告ログを出して空のクライアントを作成"""
        config_data = {
            "servers": {
                "disabled-server": {
                    "type": "http",
                    "url": "https://disabled.com/mcp",
                    "enabled": False,
                }
            }
        }
        config_file = tmp_path / "mcp.json"
        config_file.write_text(json.dumps(config_data))

        with patch(
            "qines_gai_backend.modules.ai.mcp_client.MultiServerMCPClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            result = create_mcp_client(config_file)

            # 空のconfigでクライアントが作成される
            mock_client.assert_called_once_with({})
            assert result == mock_instance

            # 警告ログが出力される
            assert "有効なMCPサーバーが設定ファイルにありません" in caplog.text


class TestGetMcpTools:
    """get_mcp_tools関数のテスト"""

    @pytest.mark.asyncio
    async def test_get_mcp_tools_001_basic_functionality(self):
        """基本的な動作確認"""
        # モッククライアントを作成
        mock_client = MagicMock()
        mock_tools = [MagicMock(name="tool1"), MagicMock(name="tool2")]
        mock_client.get_tools = AsyncMock(return_value=mock_tools)

        # get_mcp_toolsを実行
        result = await get_mcp_tools(mock_client)

        # ツールが正しく取得されている
        assert result == mock_tools
        mock_client.get_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_mcp_tools_002_exception_handling(self, caplog):
        """例外が発生した場合は空リストを返す"""
        # モッククライアントを作成
        mock_client = MagicMock()
        mock_client.get_tools = AsyncMock(side_effect=Exception("Test error"))

        # get_mcp_toolsを実行
        result = await get_mcp_tools(mock_client)

        # 空リストが返される
        assert result == []

        # エラーログが出力される
        assert "MCPツールの取得中に予期しないエラー" in caplog.text


class TestGetMcpResources:
    """get_mcp_resources関数のテスト"""

    @pytest.mark.asyncio
    async def test_get_mcp_resources_001_basic_functionality(self):
        """基本的な動作確認"""
        # モッククライアントを作成
        mock_client = MagicMock()
        mock_client.connections = {"server1": MagicMock(), "server2": MagicMock()}

        # モックリソース
        mock_resource1 = MagicMock()
        mock_resource1.metadata = {"uri": "file:///guide.md", "name": "guide"}
        mock_resource1.as_string.return_value = "Guide content"

        mock_resource2 = MagicMock()
        mock_resource2.metadata = {"uri": "file:///config.json", "name": "config"}
        mock_resource2.as_string.return_value = "{}"

        # サーバーごとのリソースを設定
        async def mock_get_resources(server_name):
            if server_name == "server1":
                return [mock_resource1]
            elif server_name == "server2":
                return [mock_resource2]
            return []

        mock_client.get_resources = mock_get_resources

        # get_mcp_resourcesを実行
        result = await get_mcp_resources(mock_client)

        # リソースが正しく取得されている
        assert len(result) == 2
        assert mock_resource1 in result
        assert mock_resource2 in result

    @pytest.mark.asyncio
    async def test_get_mcp_resources_002_server_error_handling(self, caplog):
        """サーバー単位でエラーが発生しても他のサーバーから取得を継続"""
        # モッククライアントを作成
        mock_client = MagicMock()
        mock_client.connections = {"server1": MagicMock(), "server2": MagicMock()}

        # モックリソース（server2のみ）
        mock_resource = MagicMock()
        mock_resource.metadata = {"uri": "file:///config.json", "name": "config"}

        # サーバー1はエラー、サーバー2は成功
        async def mock_get_resources(server_name):
            if server_name == "server1":
                raise Exception("Server1 error")
            elif server_name == "server2":
                return [mock_resource]
            return []

        mock_client.get_resources = mock_get_resources

        # get_mcp_resourcesを実行
        result = await get_mcp_resources(mock_client)

        # server2のリソースは取得できている
        assert len(result) == 1
        assert mock_resource in result

        # 警告ログが出力される
        assert "server1" in caplog.text
        assert "リソース取得に失敗" in caplog.text

    @pytest.mark.asyncio
    async def test_get_mcp_resources_003_exception_handling(self, caplog):
        """全体的な例外が発生した場合は空リストを返す"""
        # モッククライアントを作成
        mock_client = MagicMock()
        # connectionsアトリビュートにアクセスすると例外発生
        type(mock_client).connections = property(
            lambda self: (_ for _ in ()).throw(Exception("Test error"))
        )

        # get_mcp_resourcesを実行
        result = await get_mcp_resources(mock_client)

        # 空リストが返される
        assert result == []

        # エラーログが出力される
        assert "MCPリソースの取得中に予期しないエラー" in caplog.text
