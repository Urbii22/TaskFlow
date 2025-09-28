import pytest

from app.main import app as fastapi_app
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.user_service import create_user
from app.services.board_service import (
    create_board,
    get_board,
    get_all_boards_by_user,
    update_board,
    delete_board,
)
from app.services.column_service import (
    create_column,
    get_column,
    get_columns_by_board,
    update_column,
    delete_column,
)
from app.services.task_service import (
    create_task,
    get_task,
    update_task,
    delete_task,
    get_tasks_by_column,
)
from app.schemas.task import TaskCreate, TaskUpdate
from app.models.task import TaskPriority
from app.schemas.user import UserCreate
from app.schemas.board import BoardCreate, BoardUpdate
from app.schemas.column import ColumnCreate, ColumnUpdate


def _get_db_session_for_test():
    gen = fastapi_app.dependency_overrides[get_db]()
    db = next(gen)
    return db, gen


def _make_user(email: str = "svc@example.com") -> User:
    db, gen = _get_db_session_for_test()
    try:
        user = create_user(db, user_in=UserCreate(email=email, password="secret123"))
        return user
    finally:
        gen.close()


def test_user_service_create_duplicate_raises_value_error():
    db, gen = _get_db_session_for_test()
    try:
        _ = create_user(db, user_in=UserCreate(email="dup@x.com", password="x"))
        with pytest.raises(ValueError):
            _ = create_user(db, user_in=UserCreate(email="dup@x.com", password="x"))
    finally:
        gen.close()


def test_board_service_crud_and_ownership():
    owner = _make_user("owner@svc.com")
    other = _make_user("other@svc.com")

    db, gen = _get_db_session_for_test()
    try:
        # Create
        b = create_board(db, current_user=owner, board_in=BoardCreate(name="B"))
        # Read by owner OK
        assert get_board(db, board_id=b.id, current_user=owner) is not None
        # Read by other None
        assert get_board(db, board_id=b.id, current_user=other) is None
        # List for owner
        boards, total = get_all_boards_by_user(db, current_user=owner)
        assert total >= 1 and any(x.id == b.id for x in boards)
        # Update by owner
        b2 = update_board(db, board_id=b.id, board_in=BoardUpdate(name="B2"), current_user=owner)
        assert b2 and b2.name == "B2"
        # Update by other -> None
        assert update_board(db, board_id=b.id, board_in=BoardUpdate(name="B3"), current_user=other) is None
        # Delete by owner
        removed = delete_board(db, board_id=b.id, current_user=owner)
        assert removed and removed.id == b.id
    finally:
        gen.close()


def test_column_service_crud_and_permissions():
    owner = _make_user("colowner@svc.com")
    other = _make_user("colother@svc.com")

    db, gen = _get_db_session_for_test()
    try:
        # Board del owner
        board = create_board(db, current_user=owner, board_in=BoardCreate(name="B"))
        # Crear columna
        c = create_column(
            db,
            current_user=owner,
            column_in=ColumnCreate(name="C1", position=1, board_id=board.id),
        )
        assert c is not None
        # Obtener columna con owner OK
        assert get_column(db, column_id=c.id, current_user=owner) is not None
        # Obtener con otro -> None
        assert get_column(db, column_id=c.id, current_user=other) is None
        # Listar columnas del board
        cols, total_cols = get_columns_by_board(db, board_id=board.id, current_user=owner)
        assert total_cols == 1 and len(cols) == 1 and cols[0].id == c.id
        # Actualizar
        c2 = update_column(
            db,
            column_id=c.id,
            column_in=ColumnUpdate(name="C2", position=2),
            current_user=owner,
        )
        assert c2 and c2.name == "C2" and c2.position == 2
        # Update por otro -> None
        assert (
            update_column(db, column_id=c.id, column_in=ColumnUpdate(name="X"), current_user=other)
            is None
        )
        # Delete por otro -> None
        assert delete_column(db, column_id=c.id, current_user=other) is None
        # Delete por owner -> OK
        removed = delete_column(db, column_id=c.id, current_user=owner)
        assert removed and removed.id == c.id
    finally:
        gen.close()


def test_task_service_crud_permissions_and_list_by_column():
    owner = _make_user("taskowner@svc.com")
    other = _make_user("taskother@svc.com")

    db, gen = _get_db_session_for_test()
    try:
        # Board y columna del owner
        board = create_board(db, current_user=owner, board_in=BoardCreate(name="B"))
        column = create_column(
            db,
            current_user=owner,
            column_in=ColumnCreate(name="C1", position=1, board_id=board.id),
        )

        # Crear tarea
        t = create_task(
            db,
            current_user=owner,
            column_id=column.id,
            task_in=TaskCreate(title="T1", description="d", priority="MEDIUM", column_id=column.id),
        )
        assert t is not None

        # Obtener con owner OK, con otro None
        assert get_task(db, task_id=t.id, current_user=owner) is not None
        assert get_task(db, task_id=t.id, current_user=other) is None

        # Listar por columna
        tasks, total_tasks = get_tasks_by_column(db, column_id=column.id, current_user=owner)
        assert total_tasks == 1 and len(tasks) == 1 and tasks[0].id == t.id

        # Crear segunda tarea para probar filtros
        t_b = create_task(
            db,
            current_user=owner,
            column_id=column.id,
            task_in=TaskCreate(title="T-B", description=None, priority="HIGH", column_id=column.id),
        )
        assert t_b is not None

        # Filtro por prioridad HIGH
        only_high, total_high = get_tasks_by_column(
            db,
            column_id=column.id,
            current_user=owner,
            priority=TaskPriority.HIGH,
        )
        assert total_high >= 1 and all(str(x.priority) == "TaskPriority.HIGH" for x in only_high)

        # Asignar t a owner y filtrar por assignee
        _ = update_task(
            db,
            task_id=t.id,
            task_in=TaskUpdate(assignee_id=owner.id),
            current_user=owner,
        )
        only_owner, total_owner = get_tasks_by_column(
            db,
            column_id=column.id,
            current_user=owner,
            assignee_id=owner.id,
        )
        assert total_owner >= 1 and any(x.id == t.id for x in only_owner) and all(
            (x.assignee_id == owner.id) for x in only_owner
        )

        # Actualizar
        t2 = update_task(
            db,
            task_id=t.id,
            task_in=TaskUpdate(title="T2", priority="HIGH"),
            current_user=owner,
        )
        assert t2 and t2.title == "T2" and str(t2.priority) == "TaskPriority.HIGH"

        # Update por otro -> None
        assert (
            update_task(db, task_id=t.id, task_in=TaskUpdate(title="X"), current_user=other)
            is None
        )

        # Delete por otro -> None
        assert delete_task(db, task_id=t.id, current_user=other) is None

        # Delete por owner -> OK
        removed = delete_task(db, task_id=t.id, current_user=owner)
        assert removed and removed.id == t.id
    finally:
        gen.close()


