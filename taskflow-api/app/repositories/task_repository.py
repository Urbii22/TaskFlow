from typing import Sequence, Tuple
import re

from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.models.task import Task, TaskPriority
from app.repositories.base_repository import BaseRepository
from app.models.column import Column
from app.models.board import Board


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



    def search_tasks_by_owner(
        self,
        db: Session,
        *,
        owner_id: int,
        query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[Sequence[Task], int]:
        # Convertir entrada libre en tsquery combinada con AND para evitar errores de sintaxis
        raw_terms = [t for t in re.split(r"\s+", query.strip()) if t]
        tsquery_string = " & ".join(raw_terms) if raw_terms else ""

        # En SQLite (tests), to_tsquery/@@ no existen; aplicamos fallback con LIKE
        if db.bind and getattr(db.bind.dialect, "name", "") == "sqlite":
            like_term = f"%{query}%"
            q = (
                db.query(Task)
                .join(Column, Task.column_id == Column.id)
                .join(Board, Column.board_id == Board.id)
                .filter(Board.owner_id == owner_id)
                .filter((Task.title.ilike(like_term)) | (Task.description.ilike(like_term)))
                .order_by(Task.id.desc())
            )
        else:
            ts_query = func.to_tsquery("pg_catalog.english", tsquery_string)
            q = (
                db.query(Task)
                .join(Column, Task.column_id == Column.id)
                .join(Board, Column.board_id == Board.id)
                .filter(Board.owner_id == owner_id)
                .filter(Task.search_vector.op("@@")(ts_query))
                .order_by(Task.id.desc())
            )

        total = q.count()
        items = q.offset(skip).limit(limit).all()
        return items, total

