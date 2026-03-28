# {{ cookiecutter.project_name }}

## 概要
バックエンドテンプレートでは主に下記機能を提供します。
- FastAPIによるバックエンドAPI
  - ルーティング
  - DB接続
  - エラーハンドリング
  - ログ出力
- テスト
- linter/formatter
- ドキュメント生成

開発については下記を参照してください。
- [開発ガイド](./docs/DEVELOPMENT.md)

ディレクトリ構成については下記を参照してください。
- [ディレクトリ構成](./docs/DIRECTORY_STRUCTURE.md)

## 前提条件
- postgresqlクライアントがインストールされていること  
  MacOSの場合、下記コマンドでインストール可能です。
  ```
  brew install postgresql
  ```
- poetryがインストールされていること  
  下記コマンドでインストール可能です。
  ```
  curl -sSL https://install.python-poetry.org | python -
  ```
- (推奨)direnvがインストールされていること  
    下記コマンドでインストール可能です。
    ```
    brew install direnv
    ```
    ※ 環境変数を設定できる方法があれば、direnvは不要です。

## クイックスタート
### プロジェクトのセットアップ

1. 必要なパッケージのインストール
   ```bash
   make init
   ```
2. 環境変数の設定
   ```bash
   cp .env.sample .env
   ```
   `.env`を変更して環境変数を設定してください。  
   環境変数の意味はそれぞれ下記の通りです。
   ```
   DB_USER: データベースのユーザー名
   DB_PASSWORD: データベースのパスワード
   DB_HOST: データベースのホスト名
   DB_PORT: データベースのポート番号
   DB_NAME: データベース名

   DB_POOL_MAX_OVER_FLOW: データベースの最大オーバーフロー数
   DB_POOL_TIMEOUT: データベースのタイムアウト時間
   DB_POOL_SIZE: データベースのプールサイズ   

   LOG_LEVEL: ログレベル
   ```
   ※ DBサーバをデフォルトのまま使用する場合は`.env.sample`の値をそのまま利用してください。  
   ※ `direnv`を利用していない場合は別途環境変数を設定してください。  

   環境変数の設定が完了したら、direnvを有効にしてください。
   ```bash
   direnv allow
   ```
3. DBサーバの起動
   ```bash
   make db-up
   ```
4. DBのマイグレーション
   ```bash
   make migrate
   ```
5. 開発サーバの起動
   ```bash
   make dev
   ```

正常に起動した場合下記で動作確認が可能です。
- GET http://localhost:8000/health-check
  - レスポンス
    ```json
    {"status":"ok"}
    ```

## Makeコマンド

| コマンド | 概要 |
|-|-|
| make init | 必要なパッケージのインストールを行う |
| make db-up | DBサーバの起動を行う |
| make db-down | DBサーバの停止を行う |
| make migrate | DBのマイグレーションを行う |
| make migrate-downgrade | DBのマイグレーションをダウングレードする |
| make dev | 開発サーバの起動を行う |
| make test | テストを実行する |
| make lint | lintを実行する |
| make format | formatを実行する |
| make all | make format, make lint, make test を順に実行する |
| make docker-build | Dockerイメージのビルドを行う |
| make docker-up | Dockerコンテナの起動を行う |
| make docker-down | Dockerコンテナの停止を行う |
| make generate-migrations | `make generate-migrations message="xxx"` の形式でメッセージ付きでマイグレーションファイルの生成を行う. |
| make generate-openapi | OpenAPI.yaml形式でドキュメントを作成する |
| make generate-redoc | ReDoc形式でドキュメントを作成する |


### サンプルCRUD API
- GET http://localhost:8000/users
  - レスポンス
    ```json
    {
      "users": [
        {
          "name": "test2",
          "id": 2,
          "created_at": "2024-03-26T02:33:47.729506Z",
          "updated_at": "2024-03-26T02:33:47.729511Z"
        }
      ],
      "pagination": {
        "count": 1,
        "page": 1,
        "limit": 1
      }
    }
    ```
- POST http://localhost:8000/users
  - リクエスト
    ```json
    {
      "name": "test"
    }
    ```
  - レスポンス
    ```json
    {
      "name": "test",
      "id": 1,
      "created_at": "2024-03-26T02:33:47.729506Z",
      "updated_at": "2024-03-26T02:33:47.729511Z"
    }
    ```
- POST http://localhost:8000/users
  - リクエスト
    ```json
    {
      "name": "test"
    }
    ```
  - レスポンス
    ```json
    {
      "name": "test",
      "id": 1,
      "created_at": "2024-03-26T02:33:47.729506Z",
      "updated_at": "2024-03-26T02:33:47.729511Z"
    }
    ```
- PATCH http://localhost:8000/users/{id}
  - リクエスト
    ```json
    {
      "name": "test_update"
    }
    ```
  - レスポンス
    ```json
    {
      "name": "test_update",
      "id": 1,
      "created_at": "2024-03-26T02:33:47.729506Z",
      "updated_at": "2024-03-26T02:33:47.729511Z"
    }
    ```
- DELETE http://localhost:8000/users/{id}
