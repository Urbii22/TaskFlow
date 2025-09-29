from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_pagination_params
from app.core.cache import default_key_builder
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.pagination import Page
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import create_task, delete_task, get_task, search_tasks, update_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=Page[TaskRead])
@cache(expire=60, namespace="tasks:search", key_builder=default_key_builder)
@limiter.limit("60/minute")
def search_tasks_endpoint(
    request: Request,
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pagination: dict = Depends(get_pagination_params),
):
    items, total = search_tasks(
        db,
        current_user=current_user,
        q=q,
        skip=pagination["skip"],
        limit=pagination["limit"],
    )
    page = (pagination["skip"] // pagination["limit"]) + 1 if pagination["limit"] > 0 else 1
    return Page[TaskRead](items=list(items), total=total, page=page, size=pagination["limit"])


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_task_endpoint(
    request: Request,
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = create_task(db, current_user=current_user, column_id=task_in.column_id, task_in=task_in)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Columna no encontrada o sin permisos")
    return task


@router.get("/{task_id}", response_model=TaskRead)
@cache(expire=60, namespace="tasks:get", key_builder=default_key_builder)
def get_task_endpoint(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = get_task(db, task_id=task_id, current_user=current_user)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada o sin permisos")
    return task


@router.patch("/{task_id}", response_model=TaskRead)
@limiter.limit("30/minute")
def update_task_endpoint(
    request: Request,
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = update_task(db, task_id=task_id, task_in=task_in, current_user=current_user)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada o sin permisos")
    return task


@router.delete("/{task_id}", response_model=TaskRead)
@limiter.limit("30/minute")
def delete_task_endpoint(
    request: Request,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = delete_task(db, task_id=task_id, current_user=current_user)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada o sin permisos")
    return task
