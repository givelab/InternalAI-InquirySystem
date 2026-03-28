"""
tests/unit/crud/test_chat.py

チャット CRUD (src.crud.chat) のテスト。
pytest-postgresql の実 DB を使い、SQL レイヤの動作を検証する。
"""

import uuid
from contextlib import nullcontext as does_not_raise
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from src.crud.chat import create_chat_history, get_session_history
from src.models.chat import ChatHistory
from src.utils.logs import LogClient

_NOW = datetime(2024, 10, 1, 12, 0, 0, tzinfo=timezone.utc)


def _make_record(
    session_id: str,
    user_message: str = "質問",
    ai_response: str = "回答",
    created_at: datetime | None = None,
) -> ChatHistory:
    return ChatHistory(
        id=str(uuid.uuid4()),
        session_id=session_id,
        user_message=user_message,
        ai_response=ai_response,
        created_at=created_at or _NOW,
        updated_at=created_at or _NOW,
    )


class TestGetSessionHistory:
    @pytest.fixture(autouse=True)
    def setup(self, db: Session) -> None:
        # session-A: 3件（時刻が異なる）
        records = [
            _make_record("session-A", "質問1", "回答1", _NOW - timedelta(minutes=10)),
            _make_record("session-A", "質問2", "回答2", _NOW - timedelta(minutes=5)),
            _make_record("session-A", "質問3", "回答3", _NOW),
            # 別セッション（session-B）のレコード
            _make_record("session-B", "別セッション質問", "別セッション回答", _NOW),
        ]
        db.add_all(records)
        db.flush()

    def test_returns_records_in_chronological_order(
        self, logger: LogClient, db: Session
    ) -> None:
        """履歴が時系列（古い順）で返ること。"""
        with does_not_raise():
            history = get_session_history(logger, db, "session-A")

        assert len(history) == 3
        assert history[0].user_message == "質問1"
        assert history[1].user_message == "質問2"
        assert history[2].user_message == "質問3"

    def test_filters_by_session_id(
        self, logger: LogClient, db: Session
    ) -> None:
        """指定した session_id のレコードのみが返ること（他セッションを含まない）。"""
        history = get_session_history(logger, db, "session-A")
        assert all(h.session_id == "session-A" for h in history)

    def test_empty_for_unknown_session(
        self, logger: LogClient, db: Session
    ) -> None:
        """存在しない session_id の場合は空リストが返ること。"""
        history = get_session_history(logger, db, "session-UNKNOWN")
        assert len(history) == 0

    def test_respects_limit(
        self, logger: LogClient, db: Session
    ) -> None:
        """limit パラメータで返却件数が制限されること。"""
        history = get_session_history(logger, db, "session-A", limit=2)
        assert len(history) == 2
        # limit=2 で古い順に先頭2件が返る（reversed の結果）
        assert history[0].user_message == "質問2"
        assert history[1].user_message == "質問3"


class TestCreateChatHistory:
    def test_valid(self, logger: LogClient, db: Session) -> None:
        """正しい引数で ChatHistory が保存・返却されること。"""
        with does_not_raise():
            record = create_chat_history(
                logger,
                db,
                session_id="new-session",
                user_message="新しい質問",
                ai_response="新しい回答",
            )

        assert record.id is not None
        assert record.session_id == "new-session"
        assert record.user_message == "新しい質問"
        assert record.ai_response == "新しい回答"
        assert record.created_at is not None
        assert record.updated_at is not None

    def test_persisted_to_db(self, logger: LogClient, db: Session) -> None:
        """保存後、同じ session_id で取得できること（DB への永続化確認）。"""
        create_chat_history(logger, db, "persist-session", "保存確認質問", "保存確認回答")
        history = get_session_history(logger, db, "persist-session")
        assert len(history) == 1
        assert history[0].user_message == "保存確認質問"
        assert history[0].ai_response == "保存確認回答"

    def test_multiple_records_same_session(
        self, logger: LogClient, db: Session
    ) -> None:
        """同一セッションに複数の会話が保存できること。"""
        for i in range(3):
            create_chat_history(
                logger, db, "multi-session", f"質問{i}", f"回答{i}"
            )

        history = get_session_history(logger, db, "multi-session")
        assert len(history) == 3

    @pytest.mark.parametrize(
        "session_id, user_message, ai_response",
        [
            ("s-1", "短い質問", "短い回答"),
            ("s-2", "a" * 500, "b" * 1000),  # 長いテキスト
        ],
        ids=["short-text", "long-text"],
    )
    def test_various_text_lengths(
        self,
        logger: LogClient,
        db: Session,
        session_id: str,
        user_message: str,
        ai_response: str,
    ) -> None:
        """短いテキスト・長いテキスト（Text 型）どちらも保存できること。"""
        with does_not_raise():
            record = create_chat_history(
                logger, db, session_id, user_message, ai_response
            )
        assert record.user_message == user_message
        assert record.ai_response == ai_response
