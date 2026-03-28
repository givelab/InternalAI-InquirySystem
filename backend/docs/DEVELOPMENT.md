## 開発ガイド

- [開発ガイド](#開発ガイド)
  - [DBサーバの修正](#dbサーバの修正)
  - [サンプル実装の削除](#サンプル実装の削除)
  - [CRUD APIの修正/追加](#crud-apiの修正追加)
  - [FastAPIドキュメント確認](#fastapiドキュメント確認)


### DBサーバの修正
下記ファイルに記述のDB接続情報を修正してください
- [docker/docker-compose.yaml](../docker/docker-compose.yaml) L18 - L21
上記で修正したDB接続情報に合わせて下記ファイルを修正してください
- .env


### サンプル実装の削除
サンプル実装が必要ない場合は下記手順を行います。
1. DBの初期化
   ```bash
   make migrate-downgrade
   ```
2. サンプル実装の削除
   ```bash
   sh scripts/remove_sample_implementation.sh
   ```

### CRUD APIの修正/追加
CRUD APIの修正/追加は下記の順序で行います。
1. `models` にモデルを追加
2. `make generate-migrations message="xxx"` でマイグレーションファイルの追加
3. `schemas` にスキーマを追加
4. `crud` にCRUD処理を追加
5. `services` にビジネスロジックを追加
6. `routers` にAPIエンドポイントを追加
7. `main.py`で`router`の追加
8. `tests` にテストを追加

※ ディレクトリの詳細は[ディレクトリ構成](./DIRECTORY_STRUCTURE.md)を参照してください。  
※ 開発中には適宜`make format`, `make lint`を実行してください。

手順それぞれについて詳細を記載します。
1. `models` にモデルを追加
   - `models` ディレクトリにモデルを追加します。
   - モデルは[base.py](../src/models/base.py)の`Base`を継承して作成します。
   - 記述方法については[User](../src/models/users.py)を参照してください。
   - 記述後に[__init__.py](../src/models/__init__.py)にモデルのインポートを追加してください。(マイグレーションファイルの生成時に必要です)
2. `make generate-migrations message="xxx"` でマイグレーションファイルの追加
   - `make generate-migrations message="xxx"` でマイグレーションファイルを生成します。
   - マイグレーションファイルは`alembic`を利用して生成されます。
   - `migrations/versions`にファイルが生成されます。
3. `schemas` にスキーマを追加
   - `schemas` ディレクトリにスキーマを追加します。
   - スキーマは[base.py](../src/schemas/base.py)の`ConfiguredBaseModel`を継承して作成します。
   - 記述方法については[User](../src/schemas/users.py)を参照してください。
4. `crud` にCRUD処理を追加
   - `crud` ディレクトリにCRUD処理用のファイルを追加します。
   - 必要に応じてCRUDそれぞれに対応する処理を記述します。
     - サンプル実装は[users.py](../src/crud/users.py)の下記関数を参照してください。
     - CREATE: `create_user`
     - READ: `get_users`, `get_user`
     - UPDATE: `update_user`
     - DELETE: `delete_user`
     - 
5. `services` にビジネスロジックを追加
   - `services` ディレクトリにビジネスロジック用のファイルを追加します。
   - 必要に応じてビジネスロジックを記述します。
      - サンプル実装は[users.py](../src/services/users.py)の下記関数を参照してください。
      - CREATE: `create_user`
      - READ: `get_users`, `get_user`
      - UPDATE: `update_user`
      - DELETE: `delete_user`
6. `routers` にAPIエンドポイントを追加
   - `routers` ディレクトリにAPIエンドポイント用のファイルを追加します。
   - 必要に応じてAPIエンドポイントを記述します。
      - サンプル実装は[users.py](../src/routers/users.py)の下記関数を参照してください。
      - CREATE: `post_user`
      - READ: `get_users`, `get_user`
      - UPDATE: `patch_user`
      - DELETE: `delete_user`
7. `main.py`で`router`の追加
   - `main.py`にAPIエンドポイントを追加します。
   - `routers` ディレクトリに作成したファイルをインポートし、`app.include_router`でエンドポイントを追加します。
   - 下記のように記述してください。
     ```python
        [インポート部分]
        from src.routers import users

        [追加部分]
        app.include_router(users.router, prefix="/users")
     ```
     ※ `from src.routers.users import router` と記述することも可能ですが、複数のエンドポイントを追加する場合は`from src.routers import users`の方が混在しません。
8. `tests` にテストを追加
   - `tests` ディレクトリにテスト用のファイルを追加します。
   - 記述したファイルに対応するようにファイルを作成しテストを記述してください。

### FastAPIドキュメント確認
本テンプレートではFastAPIのドキュメントを出力しないように設定しています。  
FastAPIのドキュメントを確認する場合は下記手順で確認してください。
1. [main.py](../src/main.py)のコードを下記のように修正してください。
   ```python
   [L23]
   app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
   ->
   app = FastAPI(lifespan=lifespan)
   ```  
   ※ `docs_url=None, redoc_url=None, openapi_url=None` を削除することでドキュメントを出力するように設定可能です。([参照URL](https://fastapi.tiangolo.com/tutorial/metadata/#docs-urls))

上記修正後に下記URLでFastAPIのドキュメントを確認できます。
- http://localhost:8000/docs
- http://localhost:8000/redoc
