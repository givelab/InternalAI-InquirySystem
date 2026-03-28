from contextlib import nullcontext as does_not_raise
from datetime import datetime, timezone
from typing import Callable

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from src.crud.users import UserQuery
from src.models.users import User
from src.schemas.users import UserCreateRequest, UserUpdateRequest
from src.services.users import (
    create_user,
    delete_user,
    get_user,
    get_users,
    update_user,
)
from src.utils.exceptions import RecordNotFoundError
from src.utils.logs import LogClient


@pytest.fixture
def test_users(user_factory: Callable[..., User]) -> list[User]:
    users = []
    for i in range(0, 3):
        users.append(user_factory(id=i + 1, email=f"user{i+1}@example.com", name=f"user{i+1}"))
    return users


class TestGetUser:
    @pytest.mark.parametrize(
        "expected_idx",
        [0, 1],
    )
    def test_get_user(
        self,
        mocker: MockerFixture,
        test_users: list[User],
        expected_idx: int,
        logger: LogClient,
        db: Session,
    ) -> None:
        def side_effect_get_user(
            logger: LogClient, db: Session, user_id: int, query: UserQuery
        ) -> User:
            return test_users[user_id - 1]

        get_user_mock = mocker.patch(
            "src.services.users.users_crud.get_user", side_effect=side_effect_get_user
        )

        with does_not_raise():
            user = get_user(logger, db, test_users[expected_idx].id)

        get_user_mock.assert_called_once()
        assert user.id == test_users[expected_idx].id
        assert user.email == test_users[expected_idx].email
        assert user.name == test_users[expected_idx].name

    @pytest.mark.parametrize(
        "test_user_id",
        [
            99,
        ],
    )
    def test_not_found(
        self,
        mocker: MockerFixture,
        logger: LogClient,
        db: Session,
        test_user_id: int,
    ) -> None:
        get_user_mock = mocker.patch("src.services.users.users_crud.get_user", return_value=None)
        with pytest.raises(RecordNotFoundError):
            get_user(logger, db, test_user_id)
        get_user_mock.assert_called_once()


class TestGetUsers:
    @pytest.mark.parametrize(
        "page, limit",
        [
            (1, 10),
            (3, 1),
        ],
    )
    def test_valid(
        self,
        mocker: MockerFixture,
        test_users: list[User],
        page: int,
        limit: int,
        logger: LogClient,
        db: Session,
    ) -> None:
        def side_effect_get_users(
            _log_client: LogClient, _session: Session, _query: UserQuery
        ) -> list[User]:
            return test_users

        get_users_mock = mocker.patch(
            "src.services.users.users_crud.get_users", side_effect=side_effect_get_users
        )

        def side_effect_get_users_total_count(
            _log_client: LogClient, _session: Session, _query: UserQuery
        ) -> int:
            return len(test_users)

        get_get_users_total_count_mock = mocker.patch(
            "src.services.users.users_crud.get_users_total_count",
            side_effect=side_effect_get_users_total_count,
        )

        with does_not_raise():
            users = get_users(logger, db, page, limit)

        get_users_mock.assert_called_once()
        get_get_users_total_count_mock.assert_called_once()

        for test_user, user in zip(test_users, users.users, strict=False):
            assert user.id == test_user.id
            assert user.email == test_user.email
            assert user.name == test_user.name

    def test_not_found(
        self,
        mocker: MockerFixture,
        logger: LogClient,
        db: Session,
    ) -> None:
        get_users_mock = mocker.patch("src.services.users.users_crud.get_users", return_value=[])
        get_get_users_total_count_mock = mocker.patch(
            "src.services.users.users_crud.get_users_total_count", return_value=0
        )

        with does_not_raise():
            users = get_users(logger, db)

        get_users_mock.assert_called_once()
        get_get_users_total_count_mock.assert_called_once()
        assert len(users.users) == 0

    @pytest.mark.parametrize(
        "page, limit, expected_page, expected_limit",
        [
            (None, None, 1, 50),
            (1, None, 1, 50),
            (None, 50, 1, 50),
            (1, 50, 1, 50),
            (2, 50, 2, 50),
            (2, 10, 2, 10),
        ],
    )
    def test_query(
        self,
        mocker: MockerFixture,
        logger: LogClient,
        db: Session,
        page: int,
        limit: int,
        expected_page: int,
        expected_limit: int,
        test_users: list[User],
    ) -> None:
        def side_effect_get_users(
            _log_client: LogClient, _session: Session, query: UserQuery
        ) -> list[User]:
            assert query.page == expected_page
            assert query.limit == expected_limit
            return test_users

        get_users_mock = mocker.patch(
            "src.services.users.users_crud.get_users", side_effect=side_effect_get_users
        )

        def side_effect_get_users_total_count(
            _log_client: LogClient, _session: Session, query: UserQuery
        ) -> int:
            assert query.page == expected_page
            assert query.limit == expected_limit
            return len(test_users)

        get_get_users_total_count_mock = mocker.patch(
            "src.services.users.users_crud.get_users_total_count",
            side_effect=side_effect_get_users_total_count,
        )

        args = {
            "logger": logger,
            "db": db,
        }
        if page is not None:
            args["page"] = page
        if limit is not None:
            args["limit"] = limit
        with does_not_raise():
            get_users(**args)  # type: ignore

        get_users_mock.assert_called_once()
        get_get_users_total_count_mock.assert_called_once()


class TestCreateUser:
    @pytest.mark.parametrize(
        "new_user",
        [
            UserCreateRequest(email="user4@example.com", name="user4"),
        ],
    )
    def test_valid(
        self,
        mocker: MockerFixture,
        new_user: UserCreateRequest,
        logger: LogClient,
        db: Session,
    ) -> None:
        def side_effect_create_user(_log_client: LogClient, _session: Session, user: User) -> User:
            return User(
                id=1,
                email=user.email,
                name=user.name,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

        create_user_mock = mocker.patch(
            "src.services.users.users_crud.create_user", side_effect=side_effect_create_user
        )

        with does_not_raise():
            user = create_user(logger, db, new_user)

        create_user_mock.assert_called_once()
        assert user.id is not None
        assert user.email == new_user.email
        assert user.name == new_user.name


class TestUpdateUser:
    @pytest.mark.parametrize(
        "user_id, new_user",
        [
            (1, UserUpdateRequest(email="user1_updated@example.com", name="user1_updated")),
            (2, UserUpdateRequest(email="user2_updated@example.com", name="user2_updated")),
            (1, UserUpdateRequest(email="user1_updated@example.com")),
            (1, UserUpdateRequest(name="user1_updated")),
        ],
        ids=["update_user1", "update_user2", "update_email", "update_name"],
    )
    def test_valid(
        self,
        mocker: MockerFixture,
        user_id: int,
        new_user: UserUpdateRequest,
        test_users: list[User],
        logger: LogClient,
        db: Session,
    ) -> None:
        def side_effect_update_user(
            _log_client: LogClient,
            _session: Session,
            user_id: int,
            _query: UserQuery,
            new_user: User,
        ) -> User:
            user = test_users[user_id - 1]
            if new_user.email is not None:
                user.email = new_user.email
            if new_user.name is not None:
                user.name = new_user.name
            user.updated_at = datetime.now(timezone.utc)
            return user

        update_user_mock = mocker.patch(
            "src.services.users.users_crud.update_user", side_effect=side_effect_update_user
        )

        with does_not_raise():
            user = update_user(logger, db, user_id, new_user)

        update_user_mock.assert_called_once()
        assert user.id == test_users[user_id - 1].id
        if new_user.email is not None:
            assert user.email == new_user.email
        if new_user.name is not None:
            assert user.name == new_user.name

    @pytest.mark.parametrize(
        "user_id, new_user",
        [
            (99, UserUpdateRequest(email="user99@example.com", name="user99")),
        ],
    )
    def test_not_found(
        self,
        mocker: MockerFixture,
        user_id: int,
        new_user: UserUpdateRequest,
        logger: LogClient,
        db: Session,
    ) -> None:
        update_user_mock = mocker.patch(
            "src.services.users.users_crud.update_user", side_effect=RecordNotFoundError
        )

        with pytest.raises(RecordNotFoundError):
            update_user(logger, db, user_id, new_user)
        update_user_mock.assert_called_once()


class TestDeleteUser:
    @pytest.mark.parametrize(
        "user_id",
        [
            1,
            2,
        ],
    )
    def test_valid(
        self,
        mocker: MockerFixture,
        user_id: int,
        test_users: list[User],
        logger: LogClient,
        db: Session,
    ) -> None:
        def side_effect_delete_user(
            _log_client: LogClient, _session: Session, user_id: int, _query: UserQuery
        ) -> User:
            user = test_users[user_id - 1]
            user.deleted_at = datetime.now(timezone.utc)
            return user

        delete_user_mock = mocker.patch(
            "src.services.users.users_crud.delete_user", side_effect=side_effect_delete_user
        )

        with does_not_raise():
            delete_user(logger, db, user_id)

        delete_user_mock.assert_called_once()

    @pytest.mark.parametrize(
        "user_id",
        [
            99,
        ],
    )
    def test_not_found(
        self,
        mocker: MockerFixture,
        user_id: int,
        logger: LogClient,
        db: Session,
    ) -> None:
        delete_user_mock = mocker.patch(
            "src.services.users.users_crud.delete_user", side_effect=RecordNotFoundError
        )

        with pytest.raises(RecordNotFoundError):
            delete_user(logger, db, user_id)
        delete_user_mock.assert_called_once()
