from typing import Sequence, Tuple

from sqlalchemy.orm import Session

from app.models.column import Column
from app.repositories.base_repository import BaseRepository


class ColumnRepository(BaseRepository[Column]):
    def __init__(self) -> None:
        super().__init__(Column)

    def get_multi_by_board(
        self, db: Session, *, board_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[Sequence[Column], int]:
        query = db.query(Column).filter(Column.board_id == board_id).order_by(Column.position)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
