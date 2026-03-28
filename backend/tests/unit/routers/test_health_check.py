import pytest
from fastapi.testclient import TestClient


class TestGetHealthCheck:
    @pytest.mark.parametrize(
        "expected_status_code, expected_response",
        [
            (200, {"status": "ok"}),
        ],
    )
    def test_valid(
        self,
        client: TestClient,
        expected_status_code: int,
        expected_response: dict[str, str],
    ) -> None:
        response = client.get("/health-check")

        assert response.status_code == expected_status_code
        assert response.json() == expected_response
