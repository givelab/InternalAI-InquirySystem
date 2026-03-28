import pytest
from sqlalchemy.orm import Session

from src.utils.logs import LogClient


@pytest.fixture
def db() -> Session:
    return Session()


@pytest.fixture
def logger() -> LogClient:
    return LogClient("test_trace_id")
