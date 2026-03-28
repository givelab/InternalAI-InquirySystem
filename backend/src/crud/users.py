from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session

from src.crud.base import BaseQuery
from src.models.users import User
from src.utils.exceptions import RecordNotFoundError
from src.utils.logs import LogClient


class UserQuery(BaseQuery):
    pass


def _get_users_query(
    query: UserQuery,
    is_count: bool = False,
) -> Select[tuple[User]] | Select[tuple[int]]:
    stmt = select(User) if not is_count else select(func.count(User.id))
    stmt = stmt.where(User.deleted_at.is_(None))
    if not is_count:
        stmt = (
            stmt.order_by(desc(User.id))
            .offset((query.page - 1) * query.limit if query.page > 1 else 0)
            .limit(query.limit)
        )
    return stmt


def get_user(
    logger: LogClient,
    db: Session,
    user_id: int,
    query: UserQuery,
    with_for_update: bool = False,
) -> User | None:
    stmt = select(User).where(User.id == user_id).where(User.deleted_at.is_(None))
    if with_for_update:
        stmt = stmt.with_for_update()
    logger.debug(f"stmt: {stmt}")
    return db.execute(stmt).scalar_one_or_none()


def get_users(
    logger: LogClient,
    db: Session,
    query: UserQuery,
) -> Sequence[User]:
    stmt = _get_users_query(query)
    logger.debug(f"stmt: {stmt}")
    return db.execute(stmt).scalars().all()


def get_users_total_count(
    logger: LogClient,
    db: Session,
    query: UserQuery,
) -> int:
    stmt = _get_users_query(query, is_count=True)
    logger.debug(f"stmt: {stmt}")
    return db.execute(stmt).scalar_one() or 0


def create_user(
    logger: LogClient,
    db: Session,
    new_user: User,
) -> User:
    logger.debug(f"new_user: {new_user}")
    new_user.validate_creatable()

    db.add(new_user)
    db.flush()
    db.refresh(new_user)
    return new_user


def update_user(
    logger: LogClient,
    db: Session,
    user_id: int,
    query: UserQuery,
    new_user: User,
) -> User:
    logger.debug(f"new_user: {new_user}")
    new_user.validate_updatable()

    user = get_user(logger, db, user_id, query, with_for_update=True)
    if user is None:
        raise RecordNotFoundError(f"user_id: {user_id} is not found")

    if new_user.email is not None:
        user.email = new_user.email

    if new_user.name is not None:
        user.name = new_user.name

    user.updated_at = datetime.now(timezone.utc)

    db.flush()
    db.refresh(user)
    return user


def delete_user(
    logger: LogClient,
    db: Session,
    user_id: int,
    query: UserQuery,
) -> User:
    user = get_user(logger, db, user_id, query, with_for_update=True)
    if user is None:
        raise RecordNotFoundError(f"user_id: {user_id} is not found")

    user.deleted_at = datetime.now(timezone.utc)

    db.flush()
    db.refresh(user)
    return user
