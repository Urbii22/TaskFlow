from sqlalchemy.orm import Session

from app.models.column import Column
from app.models.user import User
from app.repositories.column_repository import ColumnRepository
from app.schemas.column import ColumnCreate, ColumnUpdate
from app.services.board_service import get_board


column_repository = ColumnRepository()


def get_columns_by_board(
    db: Session, *, board_id: int, current_user: User, skip: int = 0, limit: int = 100
):
    board = get_board(db, board_id=board_id, current_user=current_user)
    if board is None:
        return []
    return column_repository.get_multi_by_board(
        db, board_id=board_id, skip=skip, limit=limit
    )


def get_column(db: Session, *, column_id: int, current_user: User) -> Column | None:
    column = column_repository.get(db, column_id)
    if column is None:
        return None
    board = get_board(db, board_id=column.board_id, current_user=current_user)
    if board is None:
        return None
    return column


def create_column(
    db: Session, *, current_user: User, column_in: ColumnCreate
) -> Column | None:
    board = get_board(db, board_id=column_in.board_id, current_user=current_user)
    if board is None:
        return None

    data = {
        "name": column_in.name,
        "position": column_in.position,
        "board_id": column_in.board_id,
    }
    return column_repository.create(db, data)


def update_column(
    db: Session, *, column_id: int, column_in: ColumnUpdate, current_user: User
) -> Column | None:
    column = column_repository.get(db, column_id)
    if column is None:
        return None

    board = get_board(db, board_id=column.board_id, current_user=current_user)
    if board is None:
        return None

    update_data: dict = {}
    if column_in.name is not None:
        update_data["name"] = column_in.name
    if column_in.position is not None:
        update_data["position"] = column_in.position

    if not update_data:
        return column

    return column_repository.update(db, column, update_data)


def delete_column(db: Session, *, column_id: int, current_user: User) -> Column | None:
    column = column_repository.get(db, column_id)
    if column is None:
        return None

    board = get_board(db, board_id=column.board_id, current_user=current_user)
    if board is None:
        return None

    return column_repository.remove(db, column_id)


