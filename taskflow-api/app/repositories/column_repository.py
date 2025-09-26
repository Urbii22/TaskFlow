from typing import Sequence

from sqlalchemy.orm import Session

from app.models.column import Column
from app.repositories.base_repository import BaseRepository


class ColumnRepository(BaseRepository[Column]):
    def __init__(self) -> None:
        super().__init__(Column)

    def get_multi_by_board(
        self, db: Session, *, board_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[Column]:
        return (
            db.query(Column)
            .filter(Column.board_id == board_id)
            .order_by(Column.position)
            .offset(skip)
            .limit(limit)
            .all()
        )


