## ディレクトリ構成


### `src`


**`src/main.py`**

- FastAPIのエントリーポイント
- `src/router` 配下のルーターを読み込んで統合する


**`src/routers`**

- FastAPIのルーターの定義
- 通常、`schemas` の `XxxRequest` を受け取り、`XxxResponse` を返す
- `services` に `schemas` のオブジェクトを渡して、`schemas` のオブジェクトを受け取る

**`src/dependencies`**

- `routers` 層で [`Depends`](https://fastapi.tiangolo.com/tutorial/dependencies/) としてで利用される関数の定義


**`src/schemas`**

- `service`層で使用するスキーマ定義
- 通常、`router`層のリクエストとレスポンスのスキーマを定義するが、`service`層で特有の処理を行う場合は処理に対するスキーマも定義する
- 通常、`src.schemas.base.ConfiguredBaseModel` を継承する


**`src/services`**

- ビジネスロジックの定義
- `schemas` のオブジェクトを受け取り、`schemas` のオブジェクトを返す
- `crud` に `models` のオブジェクトを渡して、`models` のオブジェクトを受け取る


**`src/crud`**

- データベースの操作を定義
- `models` のオブジェクトを受け取り、`models` のオブジェクトを返す
- 2024/01 時点では、通常、DB の トランザクションは `crud` で完結する


**`src/models`**

- SQLAlchemyのモデル定義
- `crud` が授受する SQLAlchemy Model で定義されるもの以外の dataclass の定義
- ファイルはモデルごとに分割するのではなく、一定のまとまりを持ったドメインごとに分割する


**`src/apis`**

- 外部 API との通信を定義
- `apis` で定義された Entity を受け取り、`apis` で定義された Entity を返す

```
┌───────────────────┬─────────────────┐
│                   │                 │
│      routers      │   commands      │  │
│                   │                 │  │
├───────────────────┴─────────────────┤  │
│                                     │  ▼
│            services                 │
│                                     │  │
├───────────────────┬─────────────────┤  │
│                   │                 │  │
│       crud        │    apis         │  ▼
│                   │                 │
└───────────────────┴─────────────────┘

```


### `tests`


**`tests/factories`**

- FactoryBoy で定義されるテストデータの生成を定義


**`tests/integration`**
- 結合テストを定義
- `TestClient` を利用して、HTTP呼び出しを行う
- 原則として、関数のモックは行わない
- 外部通信をする場合、`requests`でのHTTPリクエストをモックしたり、外部SDKのモックを行う


**`tests/unit/routers`**

- `routers` の単体テストを定義
- `TestClient` を利用して、HTTP呼び出しを行う
- `services` のモックを行う
- リクエストに対応するパラメータが`services`に正しく渡されているかの検証、`services`から返却された値が正しくレスポンスに反映されているかの検証を行う


**`tests/unit/services`**

- `services` の単体テストを定義
- `crud`, `apis` のモックを行う
- `crud`, `apis` に正しいパラメータが渡されているかの検証、`crud`, `apis` から返却された値が `services` からの返り値に正しく反映されているかの検証を行う


**`tests/unit/crud`**
- `crud` の単体テストを定義
- 原則として、モックは行わない
- DB操作が正しく行われているかの検証を行う


**`tests/unit/apis`**
- `apis` の単体テストを定義
- `requests` のモックを行う
- `requests` に正しいパラメータが渡されているかの検証、`requests` から返却された値が `apis` からの返り値に正しく反映されているかの検証を行う


### `docker`
- Dockerfile と docker-compose.yaml を配置
- `docker-compose up` で開発環境を立ち上げることができる
- `docker-compose up` では、`app(バックエンドサーバ)` と `db(ローカル開発用DBサーバ)` の2つのコンテナが立ち上がる


### `scripts`
- 開発に利用するスクリプトを配置
- バックエンドのOpenAPIスキーマを生成するスクリプト等を配置


### `migrations`
- Alembic によるデータベースマイグレーションのスクリプトを配置
