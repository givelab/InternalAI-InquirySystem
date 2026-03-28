import random
from typing import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.users import User


def create_user(
    db: Session,
    user: User,
) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(
    db: Session,
    user_id: int,
) -> User:
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one()


@pytest.fixture
def test_users(
    db: Session,
    user_factory: Callable[..., User],
) -> list[User]:
    users = []
    num_users = random.randint(3, 10)
    for _ in range(num_users):
        user = user_factory()
        users.append(create_user(db, user))
    return users


class TestGetUser:
    @pytest.mark.parametrize(
        "expected_idx",
        [0, 1],
    )
    def test_valid(
        self,
        client: TestClient,
        expected_idx: int,
        test_users: list[User],
    ) -> None:
        response = client.get(f"/users/{test_users[expected_idx].id}")
        assert response.status_code == 200, response.text

        response_user = response.json()
        assert response_user.get("id") == test_users[expected_idx].id
        assert response_user.get("email") == test_users[expected_idx].email
        assert response_user.get("name") == test_users[expected_idx].name


class TestGetUsers:
    def test_valid(
        self,
        client: TestClient,
        db: Session,
        test_users: list[User],
    ) -> None:
        response = client.get("/users")
        assert response.status_code == 200, response.text

        response_users = response.json()["users"]
        assert len(response_users) == len(test_users)
        for response_user in response_users:
            test_user = get_user(db, response_user.get("id"))
            assert test_user is not None
            assert response_user.get("id") == test_user.id
            assert response_user.get("email") == test_user.email
            assert response_user.get("name") == test_user.name


class TestCreateUser:
    def test_valid(
        self,
        client: TestClient,
        db: Session,
    ) -> None:
        user = {
            "email": "user@example.com",
            "name": "user",
        }
        response = client.post("/users", json=user)
        assert response.status_code == 201, response.text

        response_user = response.json()
        assert response_user.get("id") is not None
        assert response_user.get("email") == user["email"]
        assert response_user.get("name") == user["name"]

        created_user = get_user(db, response_user.get("id"))
        assert created_user is not None
        assert response_user.get("id") == created_user.id
        assert response_user.get("email") == created_user.email
        assert response_user.get("name") == created_user.name


class TestUpdateUser:
    @pytest.mark.parametrize(
        "update_user",
        [
            {
                "email": "new_user1@example.com",
                "name": "new_name1",
            },
            {
                "email": "new_user2@example.com",
                "name": "new_name2",
            },
            {
                "email": "new_user@example.com",
            },
            {
                "name": "new_name",
            },
        ],
        ids=["update all 1", "update all 2", "update email", "update name"],
    )
    def test_valid(
        self,
        client: TestClient,
        db: Session,
        update_user: dict[str, str],
        test_users: list[User],
    ) -> None:
        user = test_users[0]
        response = client.patch(f"/users/{user.id}", json=update_user)
        assert response.status_code == 200, response.text

        response_user = response.json()
        assert response_user.get("id") == user.id
        if "email" in update_user:
            assert response_user.get("email") == update_user["email"]
        else:
            assert response_user.get("email") == user.email
        if "name" in update_user:
            assert response_user.get("name") == update_user["name"]
        else:
            assert response_user.get("name") == user.name

        updated_user = get_user(db, user.id)
        assert updated_user is not None
        assert response_user.get("id") == updated_user.id
        if "email" in update_user:
            assert updated_user.email == response_user.get("email")
        else:
            assert updated_user.email == user.email
        if "name" in update_user:
            assert updated_user.name == response_user.get("name")
        else:
            assert updated_user.name == user.name

    def test_not_update(
        self,
        client: TestClient,
        db: Session,
        test_users: list[User],
    ) -> None:
        user = test_users[0]
        response = client.patch(f"/users/{user.id}", json={})
        assert response.status_code == 400

        response_json = response.json()
        assert response_json.get("messages")[0] == "nothing to update"

        updated_user = get_user(db, user.id)
        assert updated_user is not None
        assert updated_user.id == user.id
        assert updated_user.email == user.email
        assert updated_user.name == user.name


class TestDeleteUser:
    def test_valid(
        self,
        client: TestClient,
        db: Session,
        test_users: list[User],
    ) -> None:
        user = test_users[0]
        response = client.delete(f"/users/{user.id}")
        assert response.status_code == 204, response.text

        deleted_user = get_user(db, user.id)
        assert deleted_user is not None
        assert deleted_user.deleted_at is not None
