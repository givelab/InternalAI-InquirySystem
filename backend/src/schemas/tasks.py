from datetime import datetime
from typing import Optional

from src.schemas.base import ConfiguredBaseModel


class TaskCreate(ConfiguredBaseModel):
    title: str


class TaskUpdate(ConfiguredBaseModel):
    title: Optional[str] = None
    is_done: Optional[bool] = None


class TaskResponse(ConfiguredBaseModel):
    id: int
    title: str
    is_done: bool
    created_at: datetime
    updated_at: datetime
