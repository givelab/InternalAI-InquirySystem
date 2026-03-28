import pytest

from src.utils.logs import LogClient


@pytest.fixture(scope="function")
def logger() -> LogClient:
    return LogClient("test_trace_id")
