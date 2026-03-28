from datetime import datetime

from src.schemas.base import ConfiguredBaseModel


class ChatRequest(ConfiguredBaseModel):
    session_id: str
    message: str


class ChatResponse(ConfiguredBaseModel):
    session_id: str
    answer: str
    created_at: datetime
