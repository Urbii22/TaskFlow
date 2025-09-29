from sqlalchemy.orm import Session

from app.core.cache import invalidate_tasks_cache_for_user
from app.models.task import Task, TaskPriority
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.column_service import get_column

task_repository = TaskRepository()


def create_task(db: Session, *, current_user: User, column_id: int, task_in: TaskCreate) -> Task | None:
    column = get_column(db, column_id=column_id, current_user=current_user)
    if column is None:
        return None

    data = {
        "title": task_in.title,
        "description": task_in.description,
        "priority": task_in.priority,
        "column_id": column_id,
    }
    if task_in.assignee_id is not None:
        data["assignee_id"] = task_in.assignee_id
    if task_in.position is not None:
        data["position"] = task_in.position
    created = task_repository.create(db, data)
    if created is not None:
        invalidate_tasks_cache_for_user(current_user.id)
    return created


def get_task(db: Session, *, task_id: int, current_user: User) -> Task | None:
    task = task_repository.get(db, task_id)
    if task is None:
        return None

    column = get_column(db, column_id=task.column_id, current_user=current_user)
    if column is None:
        return None
    return task


def update_task(db: Session, *, task_id: int, task_in: TaskUpdate, current_user: User) -> Task | None:
    task = task_repository.get(db, task_id)
    if task is None:
        return None

    column = get_column(db, column_id=task.column_id, current_user=current_user)
    if column is None:
        return None

    update_data: dict = {}
    if task_in.title is not None:
        update_data["title"] = task_in.title
    if task_in.description is not None:
        update_data["description"] = task_in.description
    if task_in.priority is not None:
        update_data["priority"] = task_in.priority
    if task_in.assignee_id is not None:
        update_data["assignee_id"] = task_in.assignee_id
    if task_in.position is not None:
        update_data["position"] = task_in.position
    if task_in.column_id is not None:
        # Validar permisos sobre la nueva columna destino
        new_column = get_column(db, column_id=task_in.column_id, current_user=current_user)
        if new_column is None:
            return None
        update_data["column_id"] = task_in.column_id

    if not update_data:
        return task

    updated = task_repository.update(db, task, update_data)
    if updated is not None:
        invalidate_tasks_cache_for_user(current_user.id)
    return updated


def delete_task(db: Session, *, task_id: int, current_user: User) -> Task | None:
    task = task_repository.get(db, task_id)
    if task is None:
        return None

    column = get_column(db, column_id=task.column_id, current_user=current_user)
    if column is None:
        return None

    removed = task_repository.remove(db, task_id)
    if removed is not None:
        invalidate_tasks_cache_for_user(current_user.id)
    return removed


def get_tasks_by_column(
    db: Session,
    *,
    column_id: int,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
    priority: TaskPriority | None = None,
    assignee_id: int | None = None,
) -> tuple[list[Task], int]:
    column = get_column(db, column_id=column_id, current_user=current_user)
    if column is None:
        return [], 0
    items, total = task_repository.get_multi_by_column(
        db,
        column_id=column_id,
        skip=skip,
        limit=limit,
        priority=priority,
        assignee_id=assignee_id,
    )
    return list(items), total


def search_tasks(
    db: Session,
    *,
    current_user: User,
    q: str,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Task], int]:
    if not q or q.strip() == "":
        return [], 0
    items, total = task_repository.search_tasks_by_owner(
        db,
        owner_id=current_user.id,
        query=q,
        skip=skip,
        limit=limit,
    )
    return list(items), total
