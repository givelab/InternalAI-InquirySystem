from contextlib import nullcontext as does_not_raise
from datetime import datetime, timezone
from typing import Callable

import pytest
from sqlalchemy.orm import Session

from src.crud.users import (
    UserQuery,
    create_user,
    delete_user,
    get_user,
    get_users,
    get_users_total_count,
    update_user,
)
from src.models.users import User
from src.utils.exceptions import ModelValidationError, RecordNotFoundError
from src.utils.logs import LogClient


@pytest.fixture
def test_users(user_factory: Callable[..., User]) -> list[User]:
    users = [
        user_factory(id=1, email="user1@example.com", name="user1"),
        user_factory(id=2, email="user2@example.com", name="user2"),
        user_factory(
            id=3, email="user3@example.com", name="user3", deleted_at=datetime.now(timezone.utc)
        ),
    ]
    return users


class TestGetUser:
    @pytest.fixture(autouse=True)
    def setup(self, db: Session, test_users: list[User]) -> None:
        db.add_all(test_users)
        db.flush()

    @pytest.mark.parametrize(
        "expected_idx",
        [0, 1],
    )
    def test_valid(
        self,
        logger: LogClient,
        db: Session,
        expected_idx: int,
        test_users: list[User],
    ) -> None:
        user = get_user(logger, db, test_users[expected_idx].id, UserQuery())
        assert user == test_users[expected_idx]

    @pytest.mark.parametrize(
        "test_user_id",
        [
            3,
            99,
        ],
        ids=["deleted", "not found"],
    )
    def test_not_found(
        self,
        logger: LogClient,
        db: Session,
        test_user_id: int,
    ) -> None:
        with does_not_raise():
            user = get_user(logger, db, test_user_id, UserQuery())
        assert user is None


class TestGetUsers:
    @pytest.fixture(autouse=True)
    def setup(self, db: Session, test_users: list[User]) -> None:
        db.add_all(test_users)
        db.flush()

    def test_valid(
        self,
        logger: LogClient,
        db: Session,
        test_users: list[User],
    ) -> None:
        with does_not_raise():
            users = get_users(logger, db, UserQuery())
        filter_users = [user for user in test_users if user.deleted_at is None]
        assert len(users) == len(filter_users)
        for user in users:
            assert user in filter_users


class TestGetUsersTotalCount:
    @pytest.fixture(autouse=True)
    def setup(self, db: Session, test_users: list[User]) -> None:
        db.add_all(test_users)
        db.flush()

    def test_valid(
        self,
        logger: LogClient,
        db: Session,
        test_users: list[User],
    ) -> None:
        with does_not_raise():
            total_count = get_users_total_count(logger, db, UserQuery())
        filter_users = [user for user in test_users if user.deleted_at is None]
        assert total_count == len(filter_users)


class TestCreateUser:
    @pytest.mark.parametrize(
        "new_user",
        [
            User(email="user1@example.com", name="user1"),
            User(email="user2@example.com", name="user2"),
        ],
        ids=["user1", "user2"],
    )
    def test_valid(
        self,
        logger: LogClient,
        db: Session,
        new_user: User,
    ) -> None:
        with does_not_raise():
            created_user = create_user(logger, db, new_user)
        assert created_user.id is not None
        assert created_user.email == new_user.email
        assert created_user.name == new_user.name
        assert created_user.created_at is not None
        assert created_user.updated_at is not None

    @pytest.mark.parametrize(
        "new_user",
        [
            User(),
            User(email="user1@example.com"),
            User(name="user1"),
        ],
        ids=["no parameters", "name is None", "email is None"],
    )
    def test_not_creatable(
        self,
        logger: LogClient,
        db: Session,
        new_user: User,
    ) -> None:
        with pytest.raises(ModelValidationError):
            create_user(logger, db, new_user)


class TestUpdateUser:
    @pytest.fixture(autouse=True)
    def setup(self, db: Session, test_users: list[User]) -> None:
        db.add_all(test_users)
        db.flush()

    @pytest.mark.parametrize(
        "expected_idx, new_user",
        [
            (0, User(email="user1_updated@example.com", name="user1_updated")),
            (1, User(email="user2_updated@example.com", name="user2_updated")),
            (0, User(email="user1_updated@example.com")),
            (0, User(name="user1_updated")),
        ],
        ids=["update all 1", "update all 2", "update email", "update name"],
    )
    def test_valid(
        self,
        logger: LogClient,
        db: Session,
        expected_idx: int,
        new_user: User,
        test_users: list[User],
    ) -> None:
        with does_not_raise():
            updated_user = update_user(
                logger, db, test_users[expected_idx].id, UserQuery(), new_user
            )
        assert updated_user.id == test_users[expected_idx].id
        if new_user.email is not None:
            assert updated_user.email == new_user.email
        if new_user.name is not None:
            assert updated_user.name == new_user.name

    @pytest.mark.parametrize(
        "expected_idx, new_user",
        [
            (0, User()),
        ],
        ids=["no parameters"],
    )
    def test_not_updatable(
        self,
        logger: LogClient,
        db: Session,
        expected_idx: int,
        new_user: User,
        test_users: list[User],
    ) -> None:
        with pytest.raises(ModelValidationError):
            update_user(logger, db, test_users[expected_idx].id, UserQuery(), new_user)

    @pytest.mark.parametrize(
        "test_user_id",
        [3, 99],
        ids=["deleted", "not found"],
    )
    def test_not_found(
        self,
        logger: LogClient,
        db: Session,
        test_user_id: int,
    ) -> None:
        with pytest.raises(RecordNotFoundError):
            update_user(
                logger,
                db,
                test_user_id,
                UserQuery(),
                User(email="user_updated@example.com", name="user_updated"),
            )


class TestDeleteUser:
    @pytest.fixture(autouse=True)
    def setup(self, db: Session, test_users: list[User]) -> None:
        db.add_all(test_users)
        db.flush()

    @pytest.mark.parametrize(
        "expected_idx",
        [0, 1],
    )
    def test_valid(
        self,
        logger: LogClient,
        db: Session,
        expected_idx: int,
        test_users: list[User],
    ) -> None:
        with does_not_raise():
            deleted_user = delete_user(logger, db, test_users[expected_idx].id, UserQuery())
        assert deleted_user.deleted_at is not None

    @pytest.mark.parametrize(
        "test_user_id",
        [3, 99],
        ids=["deleted", "not found"],
    )
    def test_not_found(
        self,
        logger: LogClient,
        db: Session,
        test_user_id: int,
    ) -> None:
        with pytest.raises(RecordNotFoundError):
            delete_user(logger, db, test_user_id, UserQuery())
