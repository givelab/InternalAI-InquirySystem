from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .settings import settings

_db_engine: Engine | None = None


def build_database_url() -> str:
    return (
        f"postgresql://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )


def open_database() -> None:
    global _db_engine
    global _session_local
    _db_engine = create_engine(
        build_database_url(),
        max_overflow=settings.db_pool_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_size=settings.db_pool_size,
    )


def close_database() -> None:
    global _db_engine
    if _db_engine is not None:
        _db_engine.dispose()
        _db_engine = None


async def get_db_engine() -> Engine:
    global _db_engine
    assert _db_engine is not None
    return _db_engine
