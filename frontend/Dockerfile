FROM python:3.12-slim

RUN apt-get update && apt-get install --no-install-recommends -y curl && \
    rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=2.0.1
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION
RUN ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# 仮想環境を作らない設定をしてから install
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-root

COPY . /app

# 今度はシステムに streamlit が入っているので直接呼べる
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
