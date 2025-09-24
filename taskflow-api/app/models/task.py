from __future__ import annotations

from datetime import datetime
import enum

from sqlalchemy import ForeignKey, String, Text, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class TaskPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    column_id: Mapped[int] = mapped_column(ForeignKey("columns.id", ondelete="CASCADE"), nullable=False, index=True)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    column = relationship("Column", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks")
    comments = relationship(
        "Comment",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="Comment.created_at",
    )



