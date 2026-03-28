from datetime import datetime

from pydantic import Field

from src.schemas.base import ConfiguredBaseModel, PaginationModel


class UserBase(ConfiguredBaseModel):
    email: str
    name: str


class UserCreateRequest(UserBase):
    pass


class UserUpdateRequest(ConfiguredBaseModel):
    email: str | None = Field(None)
    name: str | None = Field(None)


class UserResponse(UserBase):
    id: int
    email: str
    name: str
    created_at: datetime
    updated_at: datetime


class UserListResponse(ConfiguredBaseModel):
    users: list[UserResponse]
    pagination: PaginationModel
