from typing import Generator

from fastapi import Depends
from psycopg2 import errors as psycopg2_errors
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from src.database import get_db_engine
from src.utils.exceptions import ModelValidationError, RecordAlreadyExistsError


def _get_db(db: Session) -> Generator[Session, None, None]:
    try:
        yield db
        # すべての処理が終わった後にコミットする。
        # crudの処理では基本的にflushのみを行う。
        db.commit()
    except IntegrityError as e:
        if isinstance(e.orig, psycopg2_errors.UniqueViolation):
            raise RecordAlreadyExistsError("resource already exists.") from e
        if isinstance(e.orig, psycopg2_errors.NotNullViolation):
            raise ModelValidationError("required field is missing.") from e
        raise
    finally:
        db.close()


def get_db(
    db_engine: Engine = Depends(get_db_engine),
) -> Generator[Session, None, None]:
    _session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    db = _session_local()
    yield from _get_db(db)
