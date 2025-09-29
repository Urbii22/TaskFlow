from sqlalchemy.orm import Session

from app.models.board import Board
from app.models.user import User
from app.repositories.board_repository import BoardRepository
from app.schemas.board import BoardCreate, BoardUpdate

board_repository = BoardRepository()


def create_board(db: Session, *, current_user: User, board_in: BoardCreate) -> Board:
    data = {
        "name": board_in.name,
        "owner_id": current_user.id,
    }
    return board_repository.create(db, data)


def get_board(db: Session, *, board_id: int, current_user: User) -> Board | None:
    board = board_repository.get(db, board_id)
    if board is None:
        return None
    if board.owner_id != current_user.id:
        return None
    return board


def get_all_boards_by_user(
    db: Session, *, current_user: User, skip: int = 0, limit: int = 100
) -> tuple[list[Board], int]:
    items, total = board_repository.get_multi_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return list(items), total


def update_board(db: Session, *, board_id: int, board_in: BoardUpdate, current_user: User) -> Board | None:
    board = board_repository.get(db, board_id)
    if board is None:
        return None
    if board.owner_id != current_user.id:
        return None

    update_data: dict = {}
    if board_in.name is not None:
        update_data["name"] = board_in.name

    if not update_data:
        return board

    return board_repository.update(db, board, update_data)


def delete_board(db: Session, *, board_id: int, current_user: User) -> Board | None:
    board = board_repository.get(db, board_id)
    if board is None:
        return None
    if board.owner_id != current_user.id:
        return None
    return board_repository.remove(db, board_id)
