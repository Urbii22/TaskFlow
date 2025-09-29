from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_pagination_params
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.task import TaskPriority
from app.models.user import User
from app.schemas.column import ColumnCreate, ColumnRead, ColumnUpdate
from app.schemas.pagination import Page
from app.schemas.task import TaskRead
from app.services.column_service import (
    create_column,
    delete_column,
    get_column,
    update_column,
)
from app.services.task_service import get_tasks_by_column

router = APIRouter(prefix="/columns", tags=["columns"])


@router.post("/", response_model=ColumnRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_column_endpoint(
    request: Request,
    column_in: ColumnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    column = create_column(db, current_user=current_user, column_in=column_in)
    if column is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tablero no encontrado o sin permisos")
    return column


@router.get("/{column_id}", response_model=ColumnRead)
def get_column_endpoint(
    column_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    column = get_column(db, column_id=column_id, current_user=current_user)
    if column is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Columna no encontrada o sin permisos")
    return column


@router.patch("/{column_id}", response_model=ColumnRead)
@limiter.limit("30/minute")
def update_column_endpoint(
    request: Request,
    column_id: int,
    column_in: ColumnUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    column = update_column(db, column_id=column_id, column_in=column_in, current_user=current_user)
    if column is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Columna no encontrada o sin permisos")
    return column


@router.delete("/{column_id}", response_model=ColumnRead)
@limiter.limit("30/minute")
def delete_column_endpoint(
    request: Request,
    column_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    column = delete_column(db, column_id=column_id, current_user=current_user)
    if column is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Columna no encontrada o sin permisos")
    return column


@router.get("/{column_id}/tasks", response_model=Page[TaskRead])
@limiter.limit("60/minute")
def list_column_tasks_endpoint(
    request: Request,
    column_id: int,
    priority: TaskPriority | None = None,
    assignee_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pagination: dict = Depends(get_pagination_params),
):
    items, total = get_tasks_by_column(
        db,
        column_id=column_id,
        current_user=current_user,
        skip=pagination["skip"],
        limit=pagination["limit"],
        priority=priority,
        assignee_id=assignee_id,
    )
    if items == [] and total == 0:
        # Puede ser columna inexistente o sin permisos
        column = get_column(db, column_id=column_id, current_user=current_user)
        if column is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Columna no encontrada o sin permisos")
    page = (pagination["skip"] // pagination["limit"]) + 1 if pagination["limit"] > 0 else 1
    return Page[TaskRead](items=list(items), total=total, page=page, size=pagination["limit"])


