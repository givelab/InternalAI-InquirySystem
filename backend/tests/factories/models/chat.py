import uuid
from datetime import datetime, timezone

import factory

from src.models.chat import ChatHistory
from tests.factories.base import BaseFactory


class ChatHistoryFactory(BaseFactory[ChatHistory]):
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    session_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_message = factory.Faker("sentence")
    ai_response = factory.Faker("sentence")
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
