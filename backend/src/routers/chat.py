from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.dependencies.database import get_db
from src.dependencies.logs import get_logger
from src.schemas.chat import ChatRequest, ChatResponse
from src.services import chat as chat_service
from src.utils.logs import LogClient

router = APIRouter()


@router.post(
    "",
    tags=["chat"],
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="チャット送信",
    description="ユーザーの質問を受け取り、社内ナレッジベースを参照してAIが回答する",
)
def post_chat(
    request: ChatRequest,
    logger: LogClient = Depends(get_logger),
    db: Session = Depends(get_db),
) -> ChatResponse:
    try:
        return chat_service.process_chat(logger, db, request)
    except FileNotFoundError as e:
        logger.error(f"Excel file not found: {e}")
        raise HTTPException(status_code=500, detail=f"Excel file not found: {e}")
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
