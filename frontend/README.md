# aa

### 'ContainerConfig'エラー回避の手順


```
# docker compose v2以降にしてエラーを回避

# 例：Ubuntuで Docker Compose v2 をインストール
sudo apt remove docker-compose
sudo apt update
sudo apt install docker-compose-plugin

# 確認
docker compose version
# docker compose v2.×× と表示されればOK



docker system prune -af --volumes
docker compose build --no-cache
docker compose up -d


```





------------------
### 仮想環境を作らないdockerfile


```
FROM python:3.12-slim

RUN apt-get update && apt-get install --no-install-recommends -y curl && \
    rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION
RUN ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# 仮想環境を作らない設定をしてから install
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

COPY . /app

# 今度はシステムに streamlit が入っているので直接呼べる
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

```


### Dockerfile 上で poetry run streamlit を使う


```
# frontend/Dockerfile
FROM python:3.12-slim

# System packages
RUN apt-get update && apt-get install --no-install-recommends -y curl && \
    rm -rf /var/lib/apt/lists/*

# Poetry のインストール
ENV POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION
RUN ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

# pyproject.toml と poetry.lock をコピーして依存インストール
COPY pyproject.toml poetry.lock ./
# もし仮想環境をコンテナ内に作りたくない場合は↓オプションを使う
# RUN poetry config virtualenvs.create false

RUN poetry install --no-interaction --no-ansi

# アプリソースをコピー
COPY . /app

# 実行コマンドを "poetry run streamlit" に変更
CMD ["poetry", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

```
