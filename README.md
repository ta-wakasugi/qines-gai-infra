# QINeS GAI

AUTOSARドキュメントのAI検索・会話システム。さまざまなドキュメントをアップロードし、AIエージェントを通じて検索・質問応答ができる。

## サービス構成

| サービス | 役割 | ポート |
|----------|------|--------|
| frontend | Next.js 14のWebUI | 30${USER_ID:-00} |
| backend | FastAPI + LangChain/LangGraphによるAIエージェントAPI | 80${USER_ID:-00} |
| db | PostgreSQL。会話履歴・コレクション・メッセージ等のデータ保存 | 54${USER_ID:-32} |
| meilisearch | ドキュメント全文検索エンジン | 77${USER_ID:-00} |
| seaweedfs | S3互換のファイルストレージ（ドキュメント保存用）。バケットは `conf/seaweedfs-s3.json` で自動作成 | 90${USER_ID:-00} |
| mockserver | OpenAPI仕様に基づくモックAPI（フロントエンド単体開発用） | 40${USER_ID:-10} |
| keycloak | 認証・認可サーバー | 88${USER_ID:-00} |

## 立ち上げ方法

### 1. 必須ファイルの準備

#### PDFの配置
`./documents` ディレクトリにPDFファイルを配置する。
このディレクトリは、backendとfrontendコンテナの`/app/public/documents`へマウントされる。

```
qines-gai-infra/
├─ docker-compose.yml
├─ scripts/
│   └─ setup_env.sh
├─ ...
└─ documents/
  ├──R4-2-2/
  │   └── AUTOSAR_ASWS_TransformerGeneral.pdf
  │   └── ...
  ├──R22-11/
  │   └── AUTOSAR_ASWS_HealthMonitoring.pdf
  │   └── ...
  ├──R23-11/
  │   └── AUTOSAR_AP_EXP_ARAComAPI.pdf
  │   └── ...
  ├──（ユーザーからアップロードされたファイル（※必要に応じて配置））
  └──...
```

#### 環境変数の設定

`conf/` ディレクトリのテンプレートをコピーして設定ファイルを作成する。

```sh
cp conf/.env.backend.template conf/.env.backend
cp conf/.env.frontend.template conf/.env.frontend
```

各テンプレートファイル内のコメントを参照して設定すること。

#### ポート競合回避の設定（複数人開発時は必須）

同一ホストで複数の開発者が同時に開発する場合、ポート競合を避けるために以下を実行する。

```sh
./scripts/setup_env.sh
```

このスクリプトは、UNIXユーザーIDの下2桁を使って各サービスのポート番号をオフセットする。
例: USER_ID=05 の場合 → backend:8005, frontend:3005

設定される環境変数:
- `USER_ID` - ポート番号のオフセット値
- `USER_NAME` - ユーザー名
- `COMPOSE_PROJECT_NAME` - Docker Composeプロジェクト名（コンテナ名の競合回避）

**個人の開発マシンで単独開発する場合はスキップ可能。** その場合は各サービスのデフォルトポートが使用される。

### 2. 立ち上げ

```sh
docker compose up -d
```

## データのクリーンアップ

### Docker Volume の削除

```sh
docker compose down -v
```

### Meilisearch データの手動削除

Meilisearchのデータは `./data/meili_data/` にバインドマウントされているため、`docker compose down -v` を実行してもデータは削除されない。
完全にリセットするには手動で削除が必要：

```sh
rm -rf ./data/meili_data/
```

