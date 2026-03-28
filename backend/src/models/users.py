from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, LogicalDeleteMixin, TimestampMixin
from src.models.validator import validate_not_none
from src.utils.exceptions import ModelValidationError


class User(Base, TimestampMixin, LogicalDeleteMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)

    def validate_creatable(self) -> None:
        validate_not_none("email", self.email)
        validate_not_none("name", self.name)
        return None

    def validate_updatable(self) -> None:
        if self.deleted_at is not None:
            raise ModelValidationError("this user is already deleted")
        if self.email is None and self.name is None:
            raise ModelValidationError("nothing to update")
        return None
