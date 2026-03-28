.PHONY: all init dev run db-up db-down docker-up docker-down \
		docker-build docker-run test \
		lint ruff-check mypy hadolint \
		migrate migrate-downgrade \
		generate-openapi generate-redoc generate-migrations

PYTHON_VERSION?=3.11
IMAGE_NAME=backend-app

all: format lint test

format: ruff-fix

ruff-fix:
	poetry run ruff format src/ tests/ scripts/ migrations/
	poetry run ruff --fix src/ tests/ scripts/ migrations/

lint: ruff-check mypy hadolint

ruff-check:
	poetry run ruff check src/ tests/ scripts/ migrations/
	poetry run ruff format --check src/ tests/ scripts/ migrations/

mypy:
	poetry run mypy src/ tests/ scripts/ migrations/ --config-file ./pyproject.toml

hadolint:
	hadolint docker/Dockerfile

test:
	poetry run pytest tests/ -svv

init:
	poetry install --no-root --no-ansi

init-prd:
	poetry install --only main --no-root --no-ansi

dev:
	poetry run uvicorn src.main:app --reload

run:
	poetry run poetry run gunicorn src.main:app --workers 2 --threads 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:3000 --timeout 600

db-up:
	docker compose -f docker/docker-compose.yaml up db -d

db-down:
	docker compose -f docker/docker-compose.yaml down

docker-build:
	docker image build --tag ${IMAGE_NAME} --file ./docker/Dockerfile . --build-arg PYTHON_VERSION=${PYTHON_VERSION} --no-cache

docker-up:
	docker compose -f docker/docker-compose.yaml build app --no-cache
	docker compose -f docker/docker-compose.yaml up -d

docker-down:
	docker compose -f docker/docker-compose.yaml down

migrate:
	poetry run alembic upgrade head

migrate-downgrade:
	poetry run alembic downgrade base

generate-openapi:
	poetry run python -m scripts.generate_openapi

generate-redoc:
	poetry run python -m scripts.generate_redoc

generate-migrations:
	poetry run alembic revision --autogenerate -m "$(message)"
