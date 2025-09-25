from typing import Sequence

from sqlalchemy.orm import Session

from app.models.board import Board
from app.repositories.base_repository import BaseRepository


class BoardRepository(BaseRepository[Board]):
    def __init__(self) -> None:
        super().__init__(Board)

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[Board]:
        return (
            db.query(Board)
            .filter(Board.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


