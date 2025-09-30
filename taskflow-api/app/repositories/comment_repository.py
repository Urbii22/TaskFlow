from typing import Sequence, Tuple

from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.repositories.base_repository import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    def __init__(self) -> None:
        super().__init__(Comment)

    def get_multi_by_task(
        self, db: Session, *, task_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[Sequence[Comment], int]:
        query = db.query(Comment).filter(Comment.task_id == task_id, Comment.deleted_at.is_(None)).order_by(Comment.created_at)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
