from sqlalchemy.orm import Session

from src.crud import users as users_crud
from src.models.users import User
from src.schemas.base import PaginationModel
from src.schemas.users import (
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)
from src.utils.exceptions import RecordNotFoundError
from src.utils.logs import LogClient


def convert_user_model_to_schema(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _build_update_user(new_user: UserUpdateRequest) -> User:
    user = User()
    if new_user.email is not None:
        user.email = new_user.email
    if new_user.name is not None:
        user.name = new_user.name
    return user


def get_user(
    logger: LogClient,
    db: Session,
    user_id: int,
) -> UserResponse:
    user = users_crud.get_user(logger, db, user_id, users_crud.UserQuery())
    if user is None:
        raise RecordNotFoundError(f"user_id: {user_id} is not found")

    logger.debug(f"user: {user.__dict__}")
    return convert_user_model_to_schema(user)


def get_users(
    logger: LogClient,
    db: Session,
    page: int = 1,
    limit: int = 50,
) -> UserListResponse:
    query = users_crud.UserQuery(limit=limit, page=page)
    users = users_crud.get_users(logger, db, query)
    total_count = users_crud.get_users_total_count(logger, db, query)
    return UserListResponse(
        users=[convert_user_model_to_schema(user) for user in users],
        pagination=PaginationModel(count=total_count, page=page, limit=limit),
    )


def create_user(
    logger: LogClient,
    db: Session,
    new_user: UserCreateRequest,
) -> UserResponse:
    user = User(
        email=new_user.email,
        name=new_user.name,
    )

    user = users_crud.create_user(logger, db, user)
    logger.debug(f"Created user: {user}")

    return convert_user_model_to_schema(user)


def update_user(
    logger: LogClient,
    db: Session,
    user_id: int,
    new_user: UserUpdateRequest,
) -> UserResponse:
    user = _build_update_user(new_user)

    user = users_crud.update_user(logger, db, user_id, users_crud.UserQuery(), user)
    logger.debug(f"Updated user: {user}")

    return convert_user_model_to_schema(user)


def delete_user(
    logger: LogClient,
    db: Session,
    user_id: int,
) -> None:
    users_crud.delete_user(logger, db, user_id, users_crud.UserQuery())
    logger.debug(f"user_id {user_id} successfully deleted")

    return None
