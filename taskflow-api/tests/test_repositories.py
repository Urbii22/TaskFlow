import pytest

from app.main import app as fastapi_app
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.board_repository import BoardRepository
from app.repositories.column_repository import ColumnRepository
from app.models.user import Role


def _get_db_session_for_test():
    gen = fastapi_app.dependency_overrides[get_db]()
    db = next(gen)
    return db, gen


def test_user_repository_crud():
    user_repo = UserRepository()
    db, gen = _get_db_session_for_test()
    try:
        user = user_repo.create(db, {"email": "repo@example.com", "password_hash": "hash"})
        fetched = user_repo.get_by_email(db, email="repo@example.com")
        assert fetched and fetched.id == user.id
        updated = user_repo.update(db, fetched, {"role": Role.ADMIN})
        assert updated.role == Role.ADMIN
        removed = user_repo.remove(db, user.id)
        assert removed is not None
        assert user_repo.get(db, user.id) is None
    finally:
        gen.close()


def test_board_repository_get_multi_by_owner():
    user_repo = UserRepository()
    board_repo = BoardRepository()
    db, gen = _get_db_session_for_test()
    try:
        u1 = user_repo.create(db, {"email": "u1@example.com", "password_hash": "h"})
        u2 = user_repo.create(db, {"email": "u2@example.com", "password_hash": "h"})
        b1 = board_repo.create(db, {"name": "B1", "owner_id": u1.id})
        b2 = board_repo.create(db, {"name": "B2", "owner_id": u1.id})
        _ = board_repo.create(db, {"name": "B3", "owner_id": u2.id})
        boards_u1 = board_repo.get_multi_by_owner(db, owner_id=u1.id)
        assert {b.id for b in boards_u1} == {b1.id, b2.id}
    finally:
        gen.close()


def test_column_repository_get_multi_by_board_ordered():
    user_repo = UserRepository()
    board_repo = BoardRepository()
    column_repo = ColumnRepository()
    db, gen = _get_db_session_for_test()
    try:
        u = user_repo.create(db, {"email": "owner@example.com", "password_hash": "h"})
        b = board_repo.create(db, {"name": "B", "owner_id": u.id})
        c2 = column_repo.create(db, {"name": "C2", "position": 2, "board_id": b.id})
        c1 = column_repo.create(db, {"name": "C1", "position": 1, "board_id": b.id})
        cols = column_repo.get_multi_by_board(db, board_id=b.id)
        assert [c.id for c in cols] == [c1.id, c2.id]
    finally:
        gen.close()


