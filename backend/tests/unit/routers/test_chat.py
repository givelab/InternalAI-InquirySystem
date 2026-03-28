"""
tests/unit/routers/test_chat.py

POST /chat エンドポイントのルーターテスト。
chat_service.process_chat をモック化し、HTTP レイヤのみを検証する。
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from src.schemas.chat import ChatRequest, ChatResponse
from src.utils.logs import LogClient

_FIXED_NOW = datetime(2024, 10, 1, 12, 0, 0, tzinfo=timezone.utc)


class TestPostChat:
    # ── 正常系 ────────────────────────────────────────────────────────

    @pytest.mark.parametrize(
        "payload",
        [
            {"session_id": "session-abc", "message": "経費精算の申請方法を教えてください"},
            {"session_id": "session-xyz", "message": "有給休暇はどう取得しますか？"},
        ],
        ids=["expense-query", "leave-query"],
    )
    def test_valid(
        self,
        mocker: MockerFixture,
        client: TestClient,
        payload: dict[str, str],
    ) -> None:
        """正しいリクエストに対して 200 が返り、期待される JSON 構造が含まれること。"""
        expected_answer = "テスト用 AI 回答"

        def side_effect(
            _logger: LogClient, _db: Session, request: ChatRequest
        ) -> ChatResponse:
            assert request.session_id == payload["session_id"]
            assert request.message == payload["message"]
            return ChatResponse(
                session_id=request.session_id,
                answer=expected_answer,
                created_at=_FIXED_NOW,
            )

        process_chat_mock = mocker.patch(
            "src.routers.chat.chat_service.process_chat",
            side_effect=side_effect,
        )

        response = client.post("/chat", json=payload)

        process_chat_mock.assert_called_once()
        assert response.status_code == 200

        body = response.json()
        assert body["session_id"] == payload["session_id"]
        assert body["answer"] == expected_answer
        assert "created_at" in body

    # ── 異常系 ────────────────────────────────────────────────────────

    @pytest.mark.parametrize(
        "payload, description",
        [
            (
                {"message": "session_idがない"},
                "session_id が欠落している場合 422 が返ること",
            ),
            (
                {"session_id": "session-abc"},
                "message が欠落している場合 422 が返ること",
            ),
            (
                {},
                "全フィールドが欠落している場合 422 が返ること",
            ),
        ],
        ids=["missing-session_id", "missing-message", "empty-body"],
    )
    def test_missing_required_fields(
        self,
        client: TestClient,
        payload: dict[str, str],
        description: str,
    ) -> None:
        """必須パラメータが欠落している場合、422 Unprocessable Entity が返ること。"""
        response = client.post("/chat", json=payload)
        assert response.status_code == 422, description

    def test_invalid_content_type(
        self,
        client: TestClient,
    ) -> None:
        """JSON でないリクエストボディに対して 422 が返ること。"""
        response = client.post(
            "/chat",
            content="not-json",
            headers={"Content-Type": "text/plain"},
        )
        assert response.status_code == 422

    def test_service_error_propagates(
        self,
        mocker: MockerFixture,
        client: TestClient,
    ) -> None:
        """サービス層で例外が発生した場合、500 系エラーが返ること。"""
        mocker.patch(
            "src.routers.chat.chat_service.process_chat",
            side_effect=RuntimeError("OpenAI connection failed"),
        )

        response = client.post(
            "/chat",
            json={"session_id": "session-abc", "message": "テスト"},
        )
        # raise_server_exceptions=False のため 500 が返る
        assert response.status_code == 500
