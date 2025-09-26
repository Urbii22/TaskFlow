from sqlalchemy.orm import Session

from app.main import app as fastapi_app
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.board_repository import BoardRepository
from app.repositories.column_repository import ColumnRepository


def _get_db_session_for_test():
    gen = fastapi_app.dependency_overrides[get_db]()
    db = next(gen)
    return db, gen


def test_cascade_delete_board_deletes_columns():
    user_repo = UserRepository()
    board_repo = BoardRepository()
    column_repo = ColumnRepository()

    db, gen = _get_db_session_for_test()
    try:
        user = user_repo.create(db, {"email": "cascade@example.com", "password_hash": "h"})
        board = board_repo.create(db, {"name": "B", "owner_id": user.id})
        col = column_repo.create(db, {"name": "C1", "position": 1, "board_id": board.id})

        # Borrar board
        board_repo.remove(db, board.id)

        # Confirmar que la columna se eliminó por cascade
        assert column_repo.get(db, col.id) is None
    finally:
        gen.close()


