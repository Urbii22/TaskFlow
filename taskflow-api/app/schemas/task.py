from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.task import TaskPriority


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    priority: TaskPriority


class TaskCreate(TaskBase):
    column_id: int
    assignee_id: int | None = None
    position: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None
    column_id: int | None = None
    assignee_id: int | None = None
    position: int | None = None


class TaskRead(TaskBase):
    id: int
    column_id: int
    assignee_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
