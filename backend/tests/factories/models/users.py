import factory

from src.models.users import User
from tests.factories.base import BaseFactory


class UserFactory(BaseFactory[User]):
    id = factory.Sequence(lambda n: n)
    email = factory.Faker("email")
    name = factory.Faker("name")

    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")
    deleted_at = None
