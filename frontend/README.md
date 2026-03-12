# QINeS-GAI FrontEnd

## 目次

- [1. リポジトリアーキテクチャ](#1-リポジトリアーキテクチャ)
  - [ディレクトリ構成（qines-gai-frontend）](#ディレクトリ構成qines-gai-frontend)
  - [コンポーネントの構成](#コンポーネントの構成)
- [2. ローカル環境構築](#2-ローカル環境構築)
  - [2.1. 各種リポジトリのClone](#21-各種リポジトリのclone)
  - [2.2. PDFなどの必要なファイルを取得する](#22-pdfなどの必要なファイルを取得する)
  - [2.3. VSCode 拡張機能をインストールする](#23-vscode-拡張機能をインストールする)
  - [2.4. 依存関係をインストールする](#24-依存関係をインストールする)
  - [2.5. OpenAPI Client を生成する](#25-openapi-client-を生成する)
  - [2.6. アプリケーション起動](#26-アプリケーション起動)
  - [2.7. ローカル開発時の認証設定](#27-ローカル開発時の認証設定)
- [3. テスト実行方法](#3-テスト実行方法)
- [4. Tips](#4-tips)

## 1. リポジトリアーキテクチャ

QINeS-GAIのシステムは以下3つのリポジトリから構成される。

1. qines-gai-frontend: Webアプリのフロントエンド部分
2. qines-gai-backend: APIをはじめとするバックエンド部分
3. qines-gai-infra: frontend/backendをクラウド上に構築したり、frontend/backendのそれぞれを接続して起動するためのインフラ部分

### ディレクトリ構成（qines-gai-frontend）

App Router に合わせてディレクトリ構成を以下のように設計している。

```
qines-gai-frontend/
├── .husky/                 # gitリポジトリへcommitまたはpushする際に実行されるコマンドの設定
├── .vscode/                # VSCodeで開発する際の設定ファイル
├── public/                 # 静的ファイル
└── src/                    # ソースコード
    ├── actions/            # Server Action
    ├── api/                # OpenAPI クライアント
    ├── app/                # Routing files（Next.jsがページやレイアウトとして読み込むファイル）
    ├── components/         # 再利用可能な共通コンポーネント
    ├── consts/             # 定数
    ├── hooks/              # 共通カスタムフック
    ├── models/             # モデルの型定義
    └── utils/              # ユーティリティ関数
```

### コンポーネントの構成

テストコード実装の容易性・保守性向上を目的に、一部コンポーネントではビューとロジックを同ファイル内で分離した構成にしている。

- [documentSearch.tsx](./src/components/document/documentSearch.tsx)

## 2. ローカル環境構築

### 2.1. 各種リポジトリのClone

1. `qines-gai-*`のそれぞれをまとめておくディレクトリを作成する(例: `qines-gai`)
2. 1で作成したディレクトリで`1. リポジトリアーキテクチャ`に記載されているリポジトリをCloneする

   ```sh
   cd <1で作成したディレクトリ> # 例: cd qines-gai
   git clone https://git-codecommit.ap-northeast-1.amazonaws.com/v1/repos/qines-gai-frontend # frontend
   git clone https://git-codecommit.ap-northeast-1.amazonaws.com/v1/repos/qines-gai-backend # backend
   git clone https://git-codecommit.ap-northeast-1.amazonaws.com/v1/repos/qines-gai-infra # infra

   cd qines-gai-infra
   git submodule update --init --recursive # git submoduleの更新
   ```

3. (任意)VSCodeのワークスペースを設定する
   ```sh
   touch qines-gai.code-workspace
   cat <<EOF > ./qines-gai.code-workspace
   {
       "folders": [
           {
               "path": "./qines-gai-backend",
               "name": "backend",
               "color": "terminal.ansiRed"
           },
           {
               "path": "./qines-gai-frontend",
               "name": "frontend"
           },
           {
               "path": "./qines-gai-infra",
               "name": "infra"
           }
       ]
   }
   EOF
   ```

### 2.2. PDFなどの必要なファイルを取得する

以降、EC2は`QINeS-GAI-DEV-instance-shared`のインスタンスを対象とする

1. 接続するEC2に自身のSSH公開鍵がなければ管理者に連携し配置してもらう
2. EC2が停止していれば起動する
3. proxytunnelをインストールする(以下、homebrewでインストールする場合の例)
   ```sh
   brew install proxytunnel
   ```
4. EC2に接続する  
   a. AWSにログインし接続する[EC2インスタンス](https://us-west-1.console.aws.amazon.com/ec2/home?region=us-west-1#Instances:v=3;$case=tags:true%5C,client:false;$regex=tags:false%5C,client:false)のIPアドレスを取得する  
    b. `~/.ssh/config`に以下の内容を記載する  
    ※proxytunnelへのパスは`which proxytunnel`で検索可能
   ```
   Host qines-gai-dev-shared
       HostName 52.9.88.64
       User ubuntu
       Port 22
       IdentityFile <秘密鍵への絶対パス(例:`/Users/user_name/.ssh/id_rsa`)>
       ProxyCommand <proxytunnelの絶対パス(例:`/opt/homebrew/bin/proxytunnel`)> -p <プロキシへのパス(例:localhost:60088)> -d %h:%p -v
   ```
   c. VSCodeに拡張機能`Remote Development`をインストールする
   d. 手順bで作成した設定を利用してssh接続を行う
5. 以下の対応表をもとに必要なファイル/ディレクトリをダウンロードする
   ファイル | 取得元(EC2) | 配置先 | 配置例
   -- | -- | -- | --
   PDF | /home/ubuntu/infra/documents/_ | {path to qines-gai-infra}/documents/ | ~/qines-gai-infra/documents/R23_11/hoge.pdf
   meili_data | /home/ubuntu/qines-gai/meili_data | {path to qines-gai-infra}/meili_data/ | ~/qines-gai-infra/meili_data/data.ms
   .envファイル | /home/ubuntu/qines-gai/conf/_ | {path to qines-gai-infra}/conf/ | ~/qines-gai-infra/conf/.env.frontend
6. .envを生成する
   ```sh
   cd qines-gai-infra
   sh setup_env.sh
   ```

### 2.3. VSCode 拡張機能をインストールする

- .vscode/extensions.json に記載されているレコメンドの拡張機能をインストールする。

### 2.4. 依存関係をインストールする

```sh
npm i
```

### 2.5. OpenAPI Client を生成する

- openapi.json を qines-gai-backendリポジトリ から取得し、`qines-gai-frontend`ディレクトリに配置する。
- npm スクリプトを実行する。

```sh
npm run generate-openapi-zod-client
```

- `src/api/openapiClient.ts`が生成されることを確認する。

### 2.6. アプリケーション起動

1. qines-gai-infraを開き、アプリを起動する
   ```sh
   docker compose up
   ```
   ※Macを利用していて、起動に失敗する場合は以下を実行してから再度アプリを起動する
   ```sh
   export DOCKER_DEFAULT_PLATFORM=linux/amd64
   ```
2. (EC2上のリソースを起動したい場合)VSCodeのポートフォワードを設定する  
   a. ターミナルなどを開く部分から、`ポート`を選択する  
   b. ポートの転送をクリックする  
   c. ポートに`30:$USER_ID`の値を入力する($USER_IDは`.env`に記載されている2桁の数字)
3. アプリをブラウザで起動する
   a. Edgeを開き、`localhost:30:$USER_ID`を開く

### 2.7. ローカル開発時の認証設定

1. SCSKメンバに連絡し、CognitoユーザとAWS CLI用のIAMユーザを作成してもらう
2. (初回のみ)jwt-cliをインストールする
   - https://github.com/mike-engel/jwt-cli?tab=readme-ov-file#installation
3. 以下のコマンドを実行し、認証情報を取得する
   ```sh
   sh show_auth_token.sh
   ```
4. Cognitoユーザのメールアドレスとパスワードを入力する
5. クリップボードに保存されたCookieをインポートする
   - プロキシ設定したブラウザ（Edgeなど）で動作確認を行う
   - Tips: 拡張機能「[Cookie-Editor](https://microsoftedge.microsoft.com/addons/detail/cookieeditor/neaplmfkghagebokkhpjpoebhdledlfi?hl=ja)」をインストールし、Cookieをインポートすると簡単
   - 注意：Cookieに設定したTokenの有効期限は1時間であるため期限切れに注意

## 3. テスト実行方法

- フォーマット実行する。(commit 時にも自動実行される)

```sh
npm run fmt
```

- jest によるテスト実行する。

```sh
npm run test
```

- ライセンスチェック実行する。

```sh
npm run license-check
```

- 上記全て＆ビルドテスト実行する。(push 時にも自動実行される)

```sh
npm run ci
```

### 4. Tips

1. qines-gai-infraの`docuer-compose.yml`において、以下の様に書き換えておくことでローカルで変更した内容を即時取り込むことが可能になる

   - frontendの例
     - 変更前：`./frontend:/app`
     - 変更後：`../qines-gai-frontend:/app`

2. ローカル開発時は以下のDockerfileを利用することで、ローカルの環境に合わせてアプリを起動することができる

   - frontend
     - 変更前：`dockerfile: Dockerfile`
     - 変更後：`dockerfile: dev.Dockerfile`

3. infraリポジトリでpullしてもbackendが更新されないことがある
   ※ おそらくinfraリポジトリのsubmoduleへのコミット忘れ

   - 以下のコマンドを実行するなどして、backendフォルダを直接更新することができる
     ```sh
     cd backend
     git pull origin develop
     ```

4. docker compose up時にエラーとなる
   ※古いイメージが残っているケースでは、以下のコマンドを実行して解消する

   - buildを実行する
     ```sh
     docker compose down
     docker compose up --build
     ```
