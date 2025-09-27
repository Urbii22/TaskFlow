import pytest

from app.main import app as fastapi_app
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.board_repository import BoardRepository
from app.repositories.column_repository import ColumnRepository
from app.repositories.task_repository import TaskRepository
from app.models.task import TaskPriority
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


def test_task_repository_get_multi_by_column_ordered():
    user_repo = UserRepository()
    board_repo = BoardRepository()
    column_repo = ColumnRepository()
    task_repo = TaskRepository()

    db, gen = _get_db_session_for_test()
    try:
        u = user_repo.create(db, {"email": "owner2@example.com", "password_hash": "h"})
        b = board_repo.create(db, {"name": "B", "owner_id": u.id})
        c = column_repo.create(db, {"name": "C", "position": 1, "board_id": b.id})

        t2 = task_repo.create(
            db,
            {
                "title": "T2",
                "description": None,
                "priority": TaskPriority.MEDIUM,
                "position": 2,
                "column_id": c.id,
            },
        )
        t1 = task_repo.create(
            db,
            {
                "title": "T1",
                "description": None,
                "priority": TaskPriority.MEDIUM,
                "position": 1,
                "column_id": c.id,
            },
        )

        tasks = task_repo.get_multi_by_column(db, column_id=c.id)
        assert [t.id for t in tasks] == [t1.id, t2.id]
    finally:
        gen.close()


