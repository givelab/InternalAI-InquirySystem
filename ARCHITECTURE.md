# アーキテクチャ設計書 — InternalAI-InquirySystem

> このドキュメントは、システムの技術的意思決定の証跡（Design Rationale）を記録するものです。
> 「なぜこの構成を選んだのか」「どのように実装されているのか」を、
> エンジニアやクライアントが評価・拡張する際の参照資料として機能します。

---

## 1. 設計方針

このシステムの設計は、以下の3つの原則に基づいています。

| 原則 | 意図 |
|---|---|
| **シンプルさの優先** | 外部サービスへの依存を最小化し、ローカル環境で完結する構成にする |
| **疎結合** | frontend / backend / db の各コンテナは独立して起動・停止・入れ替えができる |
| **段階的拡張性** | 現状のシンプルな構成から、将来のスケールアップへの移行コストを低く保つ |

---

## 2. 技術スタックと選定理由

### FastAPI（バックエンド）

Pythonのモダンな非同期Webフレームワーク。

- **型アノテーション + Pydantic** によるリクエスト/レスポンスの自動バリデーション
- **Swagger UI** の自動生成（`/docs`）により、APIドキュメントの作成コストがゼロ
- **依存性注入（`Depends()`）** によりDB接続やロガーの注入が容易で、テスト時のモック差し替えがシンプル
- Python製のため、Pandas / OpenAI SDK など、データ処理・AI関連ライブラリとの親和性が高い

### Streamlit（フロントエンド）

Pythonだけで構築できるWebアプリフレームワーク。

- JavaScriptの知識なしに、チャットUIを迅速にプロトタイピングできる
- バックエンドチームがフロントエンドも担当できる一貫した技術スタック
- 将来的にReact等へ移行する場合も、`POST /chat` APIは変更不要

### PostgreSQL（会話履歴DB）

構造化データの永続化に特化したRDBMS。

- **会話履歴の管理のみ**に使用（ナレッジベース検索にはDBを使わない）
- `session_id` によるセッション単位の履歴取得が容易
- Docker公式イメージで環境差異なく動作する

### Pandas + openpyxl（Excel処理）

Pythonデータ処理の事実上の標準ライブラリ。

- Excelファイルを追加インフラなしに読み込み・検索できる
- 非エンジニアが更新するナレッジベースのフォーマット（Excel）と相性が良い
- ベクトルDBを使わない軽量RAGの実装基盤として機能する（詳細は後述）

### OpenAI API（gpt-4o-mini）

LLMの推論エンジンとして外部APIを利用。

- モデルをコードに含めないことで、モデルアップグレードが設定変更のみで対応可能
- `gpt-4o-mini` は高品質かつコスト効率が高く、社内FAQの用途に適している
- 温度パラメータ `0.3`（低温度）により、ハルシネーションを抑制し一貫した回答を生成

---

## 3. 「ベクトルDBなしRAG」の設計と実装

これはこのシステムの最大の技術的特徴です。

### 3-1. なぜベクトルDBを採用しなかったか

RAG（Retrieval-Augmented Generation）の一般的な実装では、ドキュメントをベクトル化してPineconeやChromaなどのベクトルDBに格納し、ユーザーの質問と意味的に近いドキュメントを検索するアプローチが取られます。

しかし本システムでは、以下の判断からベクトルDBを採用しませんでした。

| 観点 | ベクトルDB構成 | 本システムの構成 |
|---|---|---|
| ナレッジ規模 | 数万〜数十万件 | 数十〜数百件（社内FAQ） |
| インフラコスト | 外部サービス費用または自前ホスティングコスト | ゼロ |
| 運用複雑度 | 埋め込みモデルの管理、インデックス更新が必要 | Excelファイルの差し替えのみ |
| セマンティック検索の必要性 | 多義語や表記ゆれが多い場合に有効 | キーワードで十分にカバーできる |
| 初期構築コスト | 高い | 低い |

**結論:** 社内FAQ規模（数十〜数百件）のナレッジベースであれば、Pandasのキーワードマッチングで十分な検索精度が得られます。Excelファイルをそのままコンテキストとしてプロンプトに注入することで、ベクトル化・インデックス管理のオーバーヘッドを完全に排除しました。

### 3-2. Pandasフィルタリングの実装ロジック

**実装ファイル:** `backend/src/services/excel.py`

```python
_CONTEXT_COLUMNS = ["category", "subcategory", "title", "content", "keywords"]
_MAX_ROWS = 5  # プロンプトに埋め込む最大行数

def _score_row(row: pd.Series, words: list[str]) -> int:
    """行のスコア: 検索ワードが title / content / keywords に含まれる数を返す。"""
    target = f"{row['title']} {row['content']} {row['keywords']}".lower()
    return sum(1 for w in words if w in target)

def filter_relevant_rows(query: str) -> str:
    df = _load_excel()

    # 2文字以上の単語のみ対象（助詞などのノイズを除去）
    words = [w for w in query.lower().split() if len(w) >= 2]

    if not words:
        return df[_CONTEXT_COLUMNS].head(_MAX_ROWS).to_csv(index=False)

    df["_score"] = df.apply(lambda row: _score_row(row, words), axis=1)
    relevant = df[df["_score"] > 0].sort_values("_score", ascending=False)

    # マッチなしの場合は先頭5行をフォールバック
    context_df = (relevant if not relevant.empty else df).head(_MAX_ROWS)
    return context_df[_CONTEXT_COLUMNS].to_csv(index=False)
```

**処理の流れ:**

1. Excelファイルを `pandas.read_excel()` でDataFrameに読み込む
2. ユーザーのクエリを空白で分割し、2文字以上の単語のみ抽出（`は`, `を` などの助詞を除去）
3. 各行に対し、`title + content + keywords` に含まれるマッチ単語数をスコアとして算出
4. スコア > 0 の行をスコア降順でソートし、上位5行を抽出
5. マッチする行がない場合は先頭5行をフォールバックとして返す
6. 対象カラム（`category`, `subcategory`, `title`, `content`, `keywords`）のみをCSV文字列に変換して返す

**設計上の留意点:**
- `_MAX_ROWS = 5` は、OpenAIのコンテキストウィンドウを無駄に消費しないための上限です
- 検索対象を `title + content + keywords` の3カラムに限定することで、`department` や `last_updated` などの管理情報がスコアに影響しないようにしています

### 3-3. コンテキスト注入の仕組み

**実装ファイル:** `backend/src/services/chat.py`

フィルタリングされたExcelデータは、システムプロンプトに直接埋め込まれます。

```python
_SYSTEM_PROMPT_TEMPLATE = """\
あなたは社内ドキュメントに基づいて質問に答えるアシスタントです。
以下の社内ナレッジベース（CSV形式）を参照し、正確かつ簡潔に日本語で回答してください。
ナレッジベースに記載のない内容については「社内ドキュメントには該当情報が見つかりませんでした」と回答してください。

【社内ナレッジベース】
{excel_data}
"""

def process_chat(logger, db, request):
    # ① 過去10件の会話履歴を取得
    history = chat_crud.get_session_history(logger, db, request.session_id)

    # ② pandas で関連行を抽出（ベクトルDB不使用）
    excel_data = excel_service.filter_relevant_rows(request.message)

    # ③ システムプロンプト + 履歴 + 現在の質問でメッセージリストを構築
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(excel_data=excel_data)
    messages = [{"role": "system", "content": system_prompt}]

    for h in history:
        messages.append({"role": "user",      "content": h.user_message})
        messages.append({"role": "assistant", "content": h.ai_response})

    messages.append({"role": "user", "content": request.message})

    # ④ OpenAI API 呼び出し
    ai_response = openai_client.chat_completion(messages)

    # ⑤ チャット履歴を DB に保存
    record = chat_crud.create_chat_history(...)
    return ChatResponse(...)
```

**ポイント:**
- `{excel_data}` はCSV文字列として注入されます。LLMはCSVを自然に理解できるため、JSONやMarkdownへの変換コストは不要です
- 回答範囲をナレッジベースに明示的に制限する指示（「該当情報が見つかりませんでした」）により、ハルシネーションを抑制しています

### 3-4. この方式の限界と適用スケール感

| 指標 | 推奨範囲 | 限界 |
|---|---|---|
| ナレッジ件数 | 〜500件 | 1,000件超でフィルタリング精度が低下し始める |
| Excel ファイルサイズ | 〜1MB | 大きいと読み込みレイテンシが増加する |
| 検索精度 | キーワード一致で十分な場合 | 同義語・類義語・英語表記ゆれには弱い |

---

## 4. データフロー

### 4-1. リクエスト〜レスポンスの全体フロー

```
[ユーザー]
    │
    │ 質問テキスト + session_id
    ▼
[Streamlit frontend]
    │
    │ POST /chat  { session_id, message }
    ▼
[FastAPI router]  ←── LoggingMiddleware（trace_id: UUID v7 付与）
    │
    ▼
[Chat Service: process_chat()]
    │
    ├─ ① chat_crud.get_session_history(session_id, limit=10)
    │       └── SELECT FROM chat_histories WHERE session_id = ? ORDER BY created_at
    │           [PostgreSQL] → 過去会話リスト
    │
    ├─ ② excel_service.filter_relevant_rows(message)
    │       └── pandas でキーワードスコアリング
    │           [sample.xlsx] → CSV文字列（上位5行）
    │
    ├─ ③ システムプロンプト構築
    │       └── SYSTEM_PROMPT_TEMPLATE.format(excel_data=CSV)
    │           + 過去履歴を user/assistant ロールで追加
    │           + 現在の質問を user ロールで追加
    │
    ├─ ④ openai_client.chat_completion(messages)
    │       └── OpenAI API: gpt-4o-mini, temperature=0.3
    │           [External API] → AI応答テキスト
    │
    └─ ⑤ chat_crud.create_chat_history(session_id, user_message, ai_response)
            └── INSERT INTO chat_histories ...
                [PostgreSQL] → 保存完了

    │
    ▼
[ChatResponse]  { session_id, answer, created_at }
    │
    ▼
[Streamlit frontend]  → チャット画面に回答を表示
```

### 4-2. セッション管理と会話履歴の仕組み

- `session_id` はフロントエンドが生成するUUID文字列です
- 同一 `session_id` を持つリクエストは同一会話として扱われます
- 履歴は最新10件のみOpenAIへ渡します（古い履歴はコンテキストウィンドウの節約のため除外）
- DBには無制限に蓄積されるため、必要に応じて分析・検索が可能です

**DBスキーマ（`chat_histories` テーブル）:**

```sql
CREATE TABLE chat_histories (
    id          VARCHAR(36)  PRIMARY KEY,     -- UUID
    session_id  VARCHAR(36)  NOT NULL,        -- セッション識別子（インデックスあり）
    user_message TEXT        NOT NULL,        -- ユーザーの発言
    ai_response  TEXT        NOT NULL,        -- AIの回答
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL
);
CREATE INDEX ix_chat_histories_session_id ON chat_histories (session_id);
```

---

## 5. コンポーネント構成とAPI仕様

### 5-1. エンドポイント一覧

| Method | Path | 説明 |
|---|---|---|
| `GET` | `/health-check` | サービスの死活監視 |
| `POST` | `/chat` | チャットメッセージの送受信（メイン機能） |
| `GET` | `/users` | ユーザー一覧取得 |
| `POST` | `/users` | ユーザー作成 |
| `GET` | `/tasks` | タスク一覧取得 |
| `POST` | `/tasks` | タスク作成 |

**POST /chat リクエスト/レスポンス例:**

```json
// Request
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "経費精算の申請期限を教えてください"
}

// Response
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "answer": "経費精算の申請期限は、経費発生月の翌月10日までです。...",
  "created_at": "2026-03-28T10:00:00.000Z"
}
```

### 5-2. ロギング・トレーシング設計

リクエストごとに UUID v7 形式の `trace_id` を自動付与し、全ログに紐付けます。

```json
{
  "timestamp": "2026-03-28T10:00:00.000Z",
  "level": "INFO",
  "trace_id": "018e4a5b-7f3c-7000-8000-000000000001",
  "message": "session_id=550e..., history_count=3"
}
```

これにより、障害発生時のログ追跡が `trace_id` 一致で完結します。

---

## 6. セキュリティ設計

| 対策 | 実装箇所 |
|---|---|
| APIキーの環境変数管理 | `settings.py` で `.env` から読み込み、コードへのハードコードを禁止 |
| SQLインジェクション対策 | SQLAlchemy のパラメータ化クエリを使用（生SQL不使用） |
| CORS制限 | `main.py` で許可オリジンを `localhost:8000` のみに制限 |
| `.env` の除外 | `.gitignore` で `.env` をコミット対象から除外 |

---

## 7. 今後の拡張ロードマップ

現在のシンプルな構成は、将来的な拡張への足がかりとして設計されています。
各フェーズは**Dockerの疎結合性**により、他のサービスを停止せず段階的に適用できます。

### Phase 1: スケールアップ（大規模Excelへの対応）

ナレッジベースが500件を超えてきた場合の対応策:

- `excel.py` のフィルタリングロジックに **TF-IDF スコアリング** を導入
- Excelの代わりに **Google Sheets API** や **Notion API** と接続し、リアルタイムでの更新を可能にする
- `_MAX_ROWS` の動的調整や、カテゴリによる事前フィルタリングを追加

**変更スコープ:** `backend/src/services/excel.py` のみ。他のコンポーネントへの影響なし。

### Phase 2: LangChain導入とベクトルDB移行

ナレッジベースが1,000件を超え、同義語・類義語への対応が必要になった場合:

```
現在の構成:
  excel.py (pandas filter) → CSV文字列 → chat.py

移行後の構成:
  langchain_retriever.py (vector search) → Documents → chat.py
```

- `excel_service.filter_relevant_rows()` と同じインターフェース（`query: str → str`）を持つ `vector_service.retrieve()` を実装することで、`chat.py` の変更はゼロ
- ベクトルDBの選択肢: **Chroma**（ローカル、Docker対応）、**Pinecone**（マネージドサービス）
- LangChainの `VectorStoreRetriever` をラップして差し込むだけで移行完了

**変更スコープ:** `backend/src/services/` に新ファイルを追加し、`chat.py` の import 先を変更するのみ。

### Phase 3: マルチナレッジソース対応

複数部署・複数フォーマットのナレッジを統合する場合:

- Excel + PDF + Confluence + Slack アーカイブを統一的に検索するレイヤーを追加
- `excel_service` を汎用 `knowledge_service` に昇格し、ソースごとのリトリーバーを内部で切り替える
- フロントエンドのUIは変更不要（`POST /chat` のAPIは維持）

---

## 付録: 技術的負債と既知の制約

| 項目 | 現状 | 対応時期の目安 |
|---|---|---|
| Excelの毎リクエスト読み込み | リクエストごとにファイルIOが発生 | Phase 1 でキャッシュ導入 |
| セマンティック検索なし | 同義語・英語表記に対応できない | Phase 2 でベクトルDB移行 |
| CORS設定がローカル限定 | 本番デプロイ時に要変更 | デプロイ時に対応 |
| フロントエンドのセッションID管理 | ブラウザリロードで会話がリセット | 必要に応じてlocalStorage対応 |
