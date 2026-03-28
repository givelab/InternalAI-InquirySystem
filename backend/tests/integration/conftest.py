from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.dependencies.database import _get_db, get_db
from src.dependencies.settings import get_settings
from src.main import app
from src.settings import Settings
from src.utils.logs import LogClient


@pytest.fixture(scope="session")
def logger() -> LogClient:
    return LogClient()


def _client(
    app: FastAPI,
    db: Session,
) -> Generator[TestClient, None, None]:
    def mock_get_db() -> Generator[Session, None, None]:
        yield from _get_db(db)

    app.dependency_overrides[get_db] = mock_get_db

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture()
def client(
    db: Session,
) -> Generator[TestClient, None, None]:
    def mock_get_settings() -> Settings:
        return Settings()

    app.dependency_overrides[get_settings] = mock_get_settings
    yield from _client(
        app,
        db,
    )
