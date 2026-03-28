"""
tests/unit/services/test_chat.py

チャットサービス (src.services.chat) の単体テスト。
CRUD / Excel / OpenAI の各レイヤをモック化し、
ビジネスロジックのオーケストレーションのみを検証する。
"""

from datetime import datetime, timezone

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from src.models.chat import ChatHistory
from src.schemas.chat import ChatRequest, ChatResponse
from src.services.chat import process_chat
from src.utils.logs import LogClient

_FIXED_NOW = datetime(2024, 10, 1, 12, 0, 0, tzinfo=timezone.utc)


def _make_history(session_id: str, user_msg: str, ai_msg: str) -> ChatHistory:
    return ChatHistory(
        id="test-id",
        session_id=session_id,
        user_message=user_msg,
        ai_response=ai_msg,
        created_at=_FIXED_NOW,
        updated_at=_FIXED_NOW,
    )


class TestProcessChat:
    # ── 正常系 ────────────────────────────────────────────────────────

    def test_valid_no_history(
        self,
        mocker: MockerFixture,
        logger: LogClient,
        db: Session,
    ) -> None:
        """過去履歴なしの初回メッセージで正常に ChatResponse が返ること。"""
        excel_csv = "category,subcategory,title,content,keywords\n経費精算,申請手続き,申請方法,説明文,経費,精算\n"
        ai_answer = "経費は毎月25日までに申請してください。"

        get_history_mock = mocker.patch(
            "src.services.chat.chat_crud.get_session_history",
            return_value=[],
        )
        excel_mock = mocker.patch(
            "src.services.chat.excel_service.filter_relevant_rows",
            return_value=excel_csv,
        )
        openai_mock = mocker.patch(
            "src.services.chat.openai_client.chat_completion",
            return_value=ai_answer,
        )
        saved_record = _make_history("session-1", "経費申請方法は？", ai_answer)
        create_mock = mocker.patch(
            "src.services.chat.chat_crud.create_chat_history",
            return_value=saved_record,
        )

        request = ChatRequest(session_id="session-1", message="経費申請方法は？")
        result = process_chat(logger, db, request)

        assert isinstance(result, ChatResponse)
        assert result.session_id == "session-1"
        assert result.answer == ai_answer
        assert result.created_at == _FIXED_NOW

        get_history_mock.assert_called_once_with(logger, db, "session-1")
        excel_mock.assert_called_once_with("経費申請方法は？")
        openai_mock.assert_called_once()
        create_mock.assert_called_once_with(
            logger, db, session_id="session-1",
            user_message="経費申請方法は？", ai_response=ai_answer,
        )

    def test_openai_messages_include_history(
        self,
        mocker: MockerFixture,
        logger: LogClient,
        db: Session,
    ) -> None:
        """過去の会話履歴が OpenAI に渡すメッセージリストに含まれること。"""
        past_history = [
            _make_history("session-1", "有給の取り方は？", "システムから申請できます。"),
            _make_history("session-1", "何日前に申請が必要？", "3営業日前までに申請してください。"),
        ]

        mocker.patch("src.services.chat.chat_crud.get_session_history", return_value=past_history)
        mocker.patch("src.services.chat.excel_service.filter_relevant_rows", return_value="csv")
        mocker.patch(
            "src.services.chat.chat_crud.create_chat_history",
            return_value=_make_history("session-1", "続きは？", "続きの回答"),
        )

        captured_messages: list[dict] = []

        def capture_messages(messages: list[dict]) -> str:
            captured_messages.extend(messages)
            return "続きの回答"

        mocker.patch("src.services.chat.openai_client.chat_completion", side_effect=capture_messages)

        request = ChatRequest(session_id="session-1", message="続きは？")
        process_chat(logger, db, request)

        # メッセージ構造を検証:
        # [system, user(history1), assistant(history1), user(history2), assistant(history2), user(current)]
        assert len(captured_messages) == 6
        assert captured_messages[0]["role"] == "system"
        assert "csv" in captured_messages[0]["content"]  # Excel データがシステムプロンプトに含まれる

        assert captured_messages[1]["role"] == "user"
        assert captured_messages[1]["content"] == "有給の取り方は？"
        assert captured_messages[2]["role"] == "assistant"
        assert captured_messages[2]["content"] == "システムから申請できます。"

        assert captured_messages[3]["role"] == "user"
        assert captured_messages[3]["content"] == "何日前に申請が必要？"
        assert captured_messages[4]["role"] == "assistant"
        assert captured_messages[4]["content"] == "3営業日前までに申請してください。"

        assert captured_messages[5]["role"] == "user"
        assert captured_messages[5]["content"] == "続きは？"

    def test_system_prompt_contains_excel_data(
        self,
        mocker: MockerFixture,
        logger: LogClient,
        db: Session,
    ) -> None:
        """システムプロンプトに Excel から抽出したデータが埋め込まれること。"""
        expected_excel_data = "category,title\n経費精算,申請方法の説明\n"

        mocker.patch("src.services.chat.chat_crud.get_session_history", return_value=[])
        mocker.patch(
            "src.services.chat.excel_service.filter_relevant_rows",
            return_value=expected_excel_data,
        )
        mocker.patch(
            "src.services.chat.chat_crud.create_chat_history",
            return_value=_make_history("session-1", "test", "response"),
        )

        captured_system: list[str] = []

        def capture(messages: list[dict]) -> str:
            captured_system.append(messages[0]["content"])
            return "response"

        mocker.patch("src.services.chat.openai_client.chat_completion", side_effect=capture)

        process_chat(logger, db, ChatRequest(session_id="session-1", message="test"))

        assert expected_excel_data in captured_system[0]

    def test_db_save_called_with_correct_args(
        self,
        mocker: MockerFixture,
        logger: LogClient,
        db: Session,
    ) -> None:
        """DB保存時に session_id / user_message / ai_response が正しく渡されること。"""
        ai_answer = "AI からの回答テスト"

        mocker.patch("src.services.chat.chat_crud.get_session_history", return_value=[])
        mocker.patch("src.services.chat.excel_service.filter_relevant_rows", return_value="")
        mocker.patch("src.services.chat.openai_client.chat_completion", return_value=ai_answer)

        saved = _make_history("s-id", "ユーザー質問", ai_answer)
        create_mock = mocker.patch(
            "src.services.chat.chat_crud.create_chat_history",
            return_value=saved,
        )

        process_chat(logger, db, ChatRequest(session_id="s-id", message="ユーザー質問"))

        create_mock.assert_called_once_with(
            logger,
            db,
            session_id="s-id",
            user_message="ユーザー質問",
            ai_response=ai_answer,
        )
