import uuid
from typing import Sequence

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.models.chat import ChatHistory
from src.utils.logs import LogClient


def get_session_history(
    logger: LogClient,
    db: Session,
    session_id: str,
    limit: int = 10,
) -> Sequence[ChatHistory]:
    """セッションの過去の会話履歴を時系列順で返す。"""
    stmt = (
        select(ChatHistory)
        .where(ChatHistory.session_id == session_id)
        .order_by(desc(ChatHistory.created_at))
        .limit(limit)
    )
    logger.debug(f"get_session_history: session_id={session_id}")
    results = db.execute(stmt).scalars().all()
    return list(reversed(results))  # 古い順に並び替えてから返す


def create_chat_history(
    logger: LogClient,
    db: Session,
    session_id: str,
    user_message: str,
    ai_response: str,
) -> ChatHistory:
    """チャット履歴を1件保存して返す。"""
    record = ChatHistory(
        id=str(uuid.uuid4()),
        session_id=session_id,
        user_message=user_message,
        ai_response=ai_response,
    )
    logger.debug(f"create_chat_history: session_id={session_id}")
    db.add(record)
    db.flush()
    db.refresh(record)
    return record
