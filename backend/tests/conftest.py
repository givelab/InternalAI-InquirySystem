from typing import Any, Iterator
from uuid import uuid4

import psycopg
import pytest
from pytest_factoryboy import register
from sqlalchemy import NullPool, create_engine
from sqlalchemy.orm import Session, close_all_sessions, scoped_session, sessionmaker

from src.models.base import Base
from tests.factories.models.users import UserFactory

# Factory の登録
register(UserFactory)


# fixture の登録
@pytest.fixture(scope="function")
def db(postgresql: psycopg.Connection[Any]) -> Iterator[Session]:
    # ref: https://github.com/ClearcodeHQ/pytest-postgresql
    connection = f"postgresql+psycopg2://{postgresql.info.user}:@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"

    engine = create_engine(connection, echo=False, poolclass=NullPool)
    function_scope = uuid4().hex
    session_local = scoped_session(
        sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=engine,
        ),
        scopefunc=lambda: function_scope,
    )
    Base.metadata.create_all(bind=engine)

    db = session_local()
    yield db

    db.rollback()
    Base.metadata.drop_all(bind=engine)

    session_local.remove()
    close_all_sessions()
    engine.dispose()
