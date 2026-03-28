# 環境変数を読まない場合の対策


- `src/settings.py` にて、Pydantic v2 の `env_file` を正しく絶対パス指定するか、カレントディレクトリを合わせる。

    ```python
    model_config = SettingsConfigDict(
        env_file="/mnt/c/Users/yoshiakikakui/Desktop/pj_src/sdd-backend-template-main/backend/.env",
        env_file_encoding="utf-8",
    )
    
    ```
    
- **(B) OSの環境変数を export する**
    
    ```bash
    cd /mnt/c/.../backend
    source ./.venv/bin/activate  # 仮想環境に入る
    export DB_USER=postgres
    export DB_PASSWORD=postgres
    export DB_HOST=localhost
    export DB_NAME=backend_app
    make migrate
    
    ```
    
    こうすれば `.env` 不要で Pydantic が「OS に定義された環境変数」を読み込みます。