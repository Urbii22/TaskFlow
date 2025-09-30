from __future__ import annotations

from typing import Iterable

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.board import Board
from app.models.column import Column
from app.models.task import Task, TaskPriority
from app.models.user import Role, User


def get_or_create_user(db: Session, *, email: str, password: str, role: Role = Role.ADMIN) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(email=email, password_hash=get_password_hash(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_board(db: Session, *, owner_id: int, name: str) -> Board:
    board = (
        db.query(Board)
        .filter(Board.owner_id == owner_id)
        .filter(Board.name == name)
        .first()
    )
    if board:
        return board
    board = Board(name=name, owner_id=owner_id)
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


def get_or_create_column(db: Session, *, board_id: int, name: str, position: int) -> Column:
    column = (
        db.query(Column)
        .filter(Column.board_id == board_id)
        .filter(Column.name == name)
        .first()
    )
    if column:
        return column
    column = Column(name=name, position=position, board_id=board_id)
    db.add(column)
    db.commit()
    db.refresh(column)
    return column


def get_or_create_task(
    db: Session,
    *,
    column_id: int,
    title: str,
    description: str | None,
    priority: TaskPriority,
    position: int,
    assignee_id: int | None,
) -> Task:
    task = (
        db.query(Task)
        .filter(Task.column_id == column_id)
        .filter(Task.title == title)
        .first()
    )
    if task:
        return task
    task = Task(
        title=title,
        description=description,
        priority=priority,
        position=position,
        column_id=column_id,
        assignee_id=assignee_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def seed_demo_data(db: Session) -> None:
    # Usuario principal
    main_user = get_or_create_user(
        db,
        email="admin@taskflow.local",
        password="admin123",
        role=Role.ADMIN,
    )

    # Tableros de ejemplo
    board_names: Iterable[str] = (
        "Proyecto Demo",
        "Marketing",
        "Desarrollo",
    )
    boards: list[Board] = [get_or_create_board(db, owner_id=main_user.id, name=n) for n in board_names]

    # Columnas base por tablero
    default_columns: list[tuple[str, int]] = [
        ("Backlog", 1),
        ("En progreso", 2),
        ("Hecho", 3),
    ]

    for board in boards:
        columns: list[Column] = [
            get_or_create_column(db, board_id=board.id, name=name, position=pos)
            for name, pos in default_columns
        ]

        # Tareas de ejemplo por columna con distintas prioridades y asignaciones
        for column in columns:
            if column.name == "Backlog":
                get_or_create_task(
                    db,
                    column_id=column.id,
                    title="Investigar necesidades del usuario",
                    description="Entrevistas y encuestas iniciales",
                    priority=TaskPriority.LOW,
                    position=1,
                    assignee_id=main_user.id,
                )
                get_or_create_task(
                    db,
                    column_id=column.id,
                    title="Definir KPIs",
                    description="Métricas para evaluar el éxito",
                    priority=TaskPriority.MEDIUM,
                    position=2,
                    assignee_id=None,
                )
            elif column.name == "En progreso":
                get_or_create_task(
                    db,
                    column_id=column.id,
                    title="Implementar autenticación",
                    description="Login JWT y protección de endpoints",
                    priority=TaskPriority.HIGH,
                    position=1,
                    assignee_id=main_user.id,
                )
                get_or_create_task(
                    db,
                    column_id=column.id,
                    title="Configurar CI",
                    description="Pipeline básico de tests y lint",
                    priority=TaskPriority.MEDIUM,
                    position=2,
                    assignee_id=main_user.id,
                )
            elif column.name == "Hecho":
                get_or_create_task(
                    db,
                    column_id=column.id,
                    title="Diseño inicial",
                    description="Wireframes y mockups aprobados",
                    priority=TaskPriority.MEDIUM,
                    position=1,
                    assignee_id=None,
                )
                get_or_create_task(
                    db,
                    column_id=column.id,
                    title="Arreglar vulnerabilidad crítica",
                    description="Dependencia con CVE reportado",
                    priority=TaskPriority.CRITICAL,
                    position=2,
                    assignee_id=main_user.id,
                )


def main() -> None:
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()


