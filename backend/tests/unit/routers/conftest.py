from typing import Generator

import pytest
from fastapi.testclient import TestClient

from src.dependencies.database import get_db
from src.dependencies.settings import get_settings
from src.main import app
from src.settings import Settings


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def mock_get_settings() -> Settings:
        return Settings(
            db_user="test",
            db_password="test",
            db_host="test",
            db_port=5432,
            db_name="test",
            db_pool_max_overflow=10,
            db_pool_timeout=10,
            db_pool_size=5,
            openai_api_key="sk-test-dummy-key",
        )

    def mock_get_db() -> None:
        return None

    app.dependency_overrides[get_settings] = mock_get_settings
    app.dependency_overrides[get_db] = mock_get_db

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
