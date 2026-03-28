"""
チャットのコアロジック。
DB履歴取得 → Excelフィルタリング → OpenAI呼び出し → DB保存 の順で処理する。
"""

from sqlalchemy.orm import Session

from src.crud import chat as chat_crud
from src.schemas.chat import ChatRequest, ChatResponse
from src.services import excel as excel_service
from src.services import openai_client
from src.utils.logs import LogClient

_SYSTEM_PROMPT_TEMPLATE = """\
あなたは社内ドキュメントに基づいて質問に答えるアシスタントです。
以下の社内ナレッジベース（CSV形式）を参照し、正確かつ簡潔に日本語で回答してください。
ナレッジベースに記載のない内容については「社内ドキュメントには該当情報が見つかりませんでした」と回答してください。

【社内ナレッジベース】
{excel_data}
"""


def process_chat(
    logger: LogClient,
    db: Session,
    request: ChatRequest,
) -> ChatResponse:
    # ① 過去の会話履歴を取得（直近10件）
    history = chat_crud.get_session_history(logger, db, request.session_id)
    logger.info(f"session_id={request.session_id}, history_count={len(history)}")

    # ② pandas で関連行を抽出（ベクトルDB不使用）
    excel_data = excel_service.filter_relevant_rows(request.message)
    logger.debug(f"excel filter query='{request.message[:50]}'")

    # ③ OpenAI へ渡すメッセージリストを構築
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(excel_data=excel_data)
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    for h in history:
        messages.append({"role": "user", "content": h.user_message})
        messages.append({"role": "assistant", "content": h.ai_response})

    messages.append({"role": "user", "content": request.message})

    # ④ OpenAI API 呼び出し
    ai_response = openai_client.chat_completion(messages)
    logger.info(f"ai_response length={len(ai_response)}")

    # ⑤ チャット履歴を DB に保存
    record = chat_crud.create_chat_history(
        logger,
        db,
        session_id=request.session_id,
        user_message=request.message,
        ai_response=ai_response,
    )

    return ChatResponse(
        session_id=request.session_id,
        answer=ai_response,
        created_at=record.created_at,
    )
