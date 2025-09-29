from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CommentBase(BaseModel):
    text: str


class CommentCreate(CommentBase):
    task_id: int
    author_id: int


class CommentUpdate(BaseModel):
    text: str | None = None


class CommentRead(CommentBase):
    id: int
    task_id: int
    author_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
