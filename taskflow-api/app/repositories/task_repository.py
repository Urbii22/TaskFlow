from typing import Sequence

from sqlalchemy.orm import Session

from app.models.task import Task
from app.repositories.base_repository import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self) -> None:
        super().__init__(Task)

    def get_multi_by_column(
        self, db: Session, *, column_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[Task]:
        return (
            db.query(Task)
            .filter(Task.column_id == column_id)
            .order_by(Task.position)
            .offset(skip)
            .limit(limit)
            .all()
        )


