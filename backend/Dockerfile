ARG PYTHON_VERSION="3.11"

FROM python:${PYTHON_VERSION}-slim

ARG POETRY_HOME="/opt/poetry"
ARG POETRY_VERSION="2.0.1"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && \
    apt-get install --no-install-recommends -y make curl gnupg2 lsb-release && \
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg && \
    echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get install --no-install-recommends -y postgresql-15 libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org/ | python3 - --version ${POETRY_VERSION} && \
    ln -s ${POETRY_HOME}/bin/poetry /usr/local/bin/poetry && \
    poetry config virtualenvs.create false

# Create non-root user for running tests
RUN useradd -m -s /bin/bash appuser && \
    mkdir -p /app && chown appuser:appuser /app

WORKDIR /app

COPY Makefile pyproject.toml poetry.lock alembic.ini ./
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY tests/ ./tests/

RUN chown -R appuser:appuser /app

RUN make init-prd && \
    poetry install --only test --no-root --no-ansi

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
