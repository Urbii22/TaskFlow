from typing import Sequence, Tuple

from sqlalchemy.orm import Session

from app.models.task import Task, TaskPriority
from app.repositories.base_repository import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self) -> None:
        super().__init__(Task)

    def get_multi_by_column(
        self,
        db: Session,
        *,
        column_id: int,
        skip: int = 0,
        limit: int = 100,
        priority: TaskPriority | None = None,
        assignee_id: int | None = None,
    ) -> Tuple[Sequence[Task], int]:
        query = db.query(Task).filter(Task.column_id == column_id)
        if priority is not None:
            query = query.filter(Task.priority == priority)
        if assignee_id is not None:
            query = query.filter(Task.assignee_id == assignee_id)
        query = query.order_by(Task.position)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total


