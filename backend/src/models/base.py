from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    def validate_creatable(self) -> None:
        return None

    def validate_updatable(self) -> None:
        return None


class TimestampMixin(object):
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
            server_default=func.current_timestamp(),
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
            server_default=func.current_timestamp(),
        )


class LogicalDeleteMixin(object):
    @declared_attr
    def deleted_at(cls) -> Mapped[datetime | None]:
        return mapped_column(
            DateTime(timezone=True),
            default=None,
            nullable=True,
            server_default=None,
        )
