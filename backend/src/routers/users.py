from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.dependencies.database import get_db
from src.dependencies.logs import get_logger
from src.schemas.users import (
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)
from src.services import users as user_service
from src.utils.logs import LogClient

router = APIRouter()


@router.get(
    "/{user_id}",
    tags=["users"],
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="サンプルデータ詳細取得",
    description="サンプルデータの詳細を取得する",
)
def get_user(
    user_id: int,
    logger: LogClient = Depends(get_logger),
    db: Session = Depends(get_db),
) -> UserResponse:
    return user_service.get_user(logger, db, user_id)


@router.get(
    "",
    tags=["users"],
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="サンプルデータ一覧取得",
    description="サンプルデータの一覧を取得する",
)
def get_users(
    limit: int = Query(50, ge=1, le=100),
    page: int = Query(1, ge=1),
    logger: LogClient = Depends(get_logger),
    db: Session = Depends(get_db),
) -> UserListResponse:
    return user_service.get_users(logger, db, page, limit)


@router.post(
    "",
    tags=["users"],
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="サンプルデータ作成",
    description="サンプルデータを作成する",
)
def post_user(
    request: UserCreateRequest,
    logger: LogClient = Depends(get_logger),
    db: Session = Depends(get_db),
) -> UserResponse:
    return user_service.create_user(logger, db, request)


@router.patch(
    "/{user_id}",
    tags=["users"],
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="サンプルデータ更新",
    description="サンプルデータを更新する",
)
def patch_user(
    user_id: int,
    request: UserUpdateRequest,
    logger: LogClient = Depends(get_logger),
    db: Session = Depends(get_db),
) -> UserResponse:
    return user_service.update_user(logger, db, user_id, request)


@router.delete(
    "/{user_id}",
    tags=["users"],
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="サンプルデータ削除",
    description="サンプルデータを削除する",
)
def delete_user(
    user_id: int,
    logger: LogClient = Depends(get_logger),
    db: Session = Depends(get_db),
) -> None:
    return user_service.delete_user(logger, db, user_id)
