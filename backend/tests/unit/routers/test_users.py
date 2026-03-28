from datetime import datetime, timezone
from typing import Callable

import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from src.models.users import User
from src.schemas.base import PaginationModel
from src.schemas.users import (
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)
from src.services.users import convert_user_model_to_schema
from src.utils.logs import LogClient


@pytest.fixture
def test_users(user_factory: Callable[..., User]) -> list[User]:
    users = [
        user_factory(id=1, email="user1@example.com", name="user1"),
        user_factory(id=2, email="user2@example.com", name="user2"),
        user_factory(id=3, email="user3@example.com", name="user3"),
    ]
    return users


class TestGetUser:
    @pytest.mark.parametrize(
        "expected_idx",
        [0, 1],
    )
    def test_valid(
        self,
        expected_idx: int,
        mocker: MockerFixture,
        client: TestClient,
        test_users: list[User],
    ) -> None:
        def side_effect_get_user(_logger: LogClient, _db: Session, user_id: int) -> UserResponse:
            assert user_id == test_users[expected_idx].id
            return convert_user_model_to_schema(test_users[expected_idx])

        get_user_mock = mocker.patch(
            "src.routers.users.user_service.get_user", side_effect=side_effect_get_user
        )

        response = client.get(f"/users/{test_users[expected_idx].id}")

        get_user_mock.assert_called_once()
        assert response.status_code == 200
        response_user = response.json()
        assert response_user["id"] == test_users[expected_idx].id
        assert response_user["email"] == test_users[expected_idx].email
        assert response_user["name"] == test_users[expected_idx].name


class TestGetUsers:
    def test_valid(
        self,
        mocker: MockerFixture,
        client: TestClient,
        test_users: list[User],
    ) -> None:
        def side_effect_get_users(
            _logger: LogClient, _db: Session, page: int, limit: int
        ) -> UserListResponse:
            return UserListResponse(
                users=[convert_user_model_to_schema(test_user) for test_user in test_users],
                pagination=PaginationModel(page=page, limit=limit, count=len(test_users)),
            )

        get_users_mock = mocker.patch(
            "src.routers.users.user_service.get_users", side_effect=side_effect_get_users
        )

        response = client.get("/users")

        get_users_mock.assert_called_once()
        assert response.status_code == 200
        response_users = response.json()

        for test_user, response_user in zip(test_users, response_users["users"], strict=True):
            assert response_user["id"] == test_user.id
            assert response_user["email"] == test_user.email
            assert response_user["name"] == test_user.name

    @pytest.mark.parametrize(
        "page, limit, expected_page, expected_limit",
        [
            (None, None, 1, 50),
            (2, None, 2, 50),
            (None, 5, 1, 5),
            (2, 5, 2, 5),
        ],
    )
    def test_query(
        self,
        mocker: MockerFixture,
        client: TestClient,
        test_users: list[User],
        page: int,
        limit: int,
        expected_page: int,
        expected_limit: int,
    ) -> None:
        def side_effect_get_users(
            _logger: LogClient, _db: Session, page: int, limit: int
        ) -> UserListResponse:
            assert page == expected_page
            assert limit == expected_limit
            return UserListResponse(
                users=[], pagination=PaginationModel(page=page, limit=limit, count=0)
            )

        get_users_mock = mocker.patch(
            "src.routers.users.user_service.get_users", side_effect=side_effect_get_users
        )

        query = ""
        if page is not None:
            query += f"page={page}"
        if limit is not None:
            if len(query) > 0:
                query += "&"
            query += f"limit={limit}"
        response = client.get(f"/users?{query}")

        get_users_mock.assert_called_once()
        assert response.status_code == 200


class TestPostUser:
    @pytest.mark.parametrize(
        "new_user",
        [
            {
                "email": "user1@example.com",
                "name": "user1",
            },
            {
                "email": "user2@example.com",
                "name": "user2",
            },
        ],
        ids=["create all parameters 1", "create all parameters 2"],
    )
    def test_valid(
        self,
        mocker: MockerFixture,
        client: TestClient,
        new_user: dict[str, str],
    ) -> None:
        def side_effect_create_user(
            _logger: LogClient, _db: Session, user: UserCreateRequest
        ) -> UserResponse:
            return convert_user_model_to_schema(
                User(
                    id=1,
                    email=user.email,
                    name=user.name,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

        create_user_mock = mocker.patch(
            "src.routers.users.user_service.create_user",
            side_effect=side_effect_create_user,
        )

        response = client.post("/users", json=new_user, follow_redirects=False)

        create_user_mock.assert_called_once()
        assert response.status_code == 201
        response_user = response.json()
        assert response_user["id"] == 1
        assert response_user["email"] == new_user["email"]
        assert response_user["name"] == new_user["name"]


class TestPatchUser:
    @pytest.mark.parametrize(
        "expected_idx, new_user",
        [
            (0, {"email": "user1_updated@example.com", "name": "user1_updated"}),
            (1, {"email": "user2_updated@example.com", "name": "user2_updated"}),
            (0, {"email": "user1_updated@example.com"}),
            (0, {"name": "user1_updated"}),
        ],
        ids=["update all 1", "update all 2", "update email", "update name"],
    )
    def test_valid(
        self,
        expected_idx: int,
        mocker: MockerFixture,
        client: TestClient,
        test_users: list[User],
        new_user: dict[str, str],
    ) -> None:
        def side_effect_update_user(
            _logger: LogClient, _db: Session, user_id: int, new_user: UserUpdateRequest
        ) -> UserResponse:
            assert user_id == test_users[expected_idx].id
            user = test_users[expected_idx]
            if new_user.email is not None:
                user.email = new_user.email
            if new_user.name is not None:
                user.name = new_user.name
            user.updated_at = datetime.now(timezone.utc)
            return convert_user_model_to_schema(user)

        update_user_mock = mocker.patch(
            "src.routers.users.user_service.update_user",
            side_effect=side_effect_update_user,
        )

        response = client.patch(
            f"/users/{test_users[expected_idx].id}", json=new_user, follow_redirects=False
        )

        update_user_mock.assert_called_once()
        assert response.status_code == 200
        response_user = response.json()
        assert response_user["id"] == test_users[expected_idx].id
        if new_user.get("email") is not None:
            assert response_user["email"] == new_user["email"]
        if new_user.get("name") is not None:
            assert response_user["name"] == new_user["name"]


class TestDeleteUser:
    @pytest.mark.parametrize(
        "expected_idx",
        [0, 1],
    )
    def test_valid(
        self,
        expected_idx: int,
        mocker: MockerFixture,
        client: TestClient,
        test_users: list[User],
    ) -> None:
        def side_effect_delete_user(_logger: LogClient, _db: Session, user_id: int) -> None:
            assert user_id == test_users[expected_idx].id
            return None

        delete_user_mock = mocker.patch(
            "src.routers.users.user_service.delete_user",
            side_effect=side_effect_delete_user,
        )

        response = client.delete(f"/users/{test_users[expected_idx].id}")

        delete_user_mock.assert_called_once()
        assert response.status_code == 204
