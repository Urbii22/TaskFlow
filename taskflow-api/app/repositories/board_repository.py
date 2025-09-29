from typing import Sequence, Tuple

from sqlalchemy.orm import Session

from app.models.board import Board
from app.repositories.base_repository import BaseRepository


class BoardRepository(BaseRepository[Board]):
    def __init__(self) -> None:
        super().__init__(Board)

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[Sequence[Board], int]:
        query = db.query(Board).filter(Board.owner_id == owner_id)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
