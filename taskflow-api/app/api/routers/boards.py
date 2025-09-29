from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_pagination_params
from app.core.cache import default_key_builder
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.board import BoardCreate, BoardRead, BoardUpdate
from app.schemas.column import ColumnRead
from app.schemas.pagination import Page
from app.services.board_service import (
    create_board,
    delete_board,
    get_all_boards_by_user,
    get_board,
    update_board,
)
from app.services.column_service import get_columns_by_board

router = APIRouter(prefix="/boards", tags=["boards"])


@router.post("/", response_model=BoardRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_board_endpoint(
    request: Request,
    board_in: BoardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_board(db, current_user=current_user, board_in=board_in)


@router.get("/", response_model=Page[BoardRead])
@cache(expire=60, namespace="boards:list", key_builder=default_key_builder)
@limiter.limit("60/minute")
def list_boards_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pagination: dict = Depends(get_pagination_params),
):
    items, total = get_all_boards_by_user(
        db, current_user=current_user, skip=pagination["skip"], limit=pagination["limit"]
    )
    page = (pagination["skip"] // pagination["limit"]) + 1 if pagination["limit"] > 0 else 1
    return Page[BoardRead](items=list(items), total=total, page=page, size=pagination["limit"])


@router.get("/{board_id}", response_model=BoardRead)
def get_board_endpoint(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    board = get_board(db, board_id=board_id, current_user=current_user)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tablero no encontrado")
    return board


@router.patch("/{board_id}", response_model=BoardRead)
@limiter.limit("30/minute")
def update_board_endpoint(
    request: Request,
    board_id: int,
    board_in: BoardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    board = update_board(db, board_id=board_id, board_in=board_in, current_user=current_user)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tablero no encontrado o sin permisos")
    return board


@router.delete("/{board_id}", response_model=BoardRead)
@limiter.limit("30/minute")
def delete_board_endpoint(
    request: Request,
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    board = delete_board(db, board_id=board_id, current_user=current_user)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tablero no encontrado o sin permisos")
    return board


@router.get("/{board_id}/columns", response_model=Page[ColumnRead])
@cache(expire=60, namespace="boards:columns", key_builder=default_key_builder)
@limiter.limit("60/minute")
def list_board_columns_endpoint(
    request: Request,
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pagination: dict = Depends(get_pagination_params),
):
    # La función de servicio valida ownership internamente
    items, total = get_columns_by_board(
        db, board_id=board_id, current_user=current_user, skip=pagination["skip"], limit=pagination["limit"]
    )
    if items == [] and total == 0:
        # Puede ser tablero inexistente o sin permisos; devolvemos 404 para no filtrar información
        board = get_board(db, board_id=board_id, current_user=current_user)
        if board is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tablero no encontrado o sin permisos")
    page = (pagination["skip"] // pagination["limit"]) + 1 if pagination["limit"] > 0 else 1
    return Page[ColumnRead](items=list(items), total=total, page=page, size=pagination["limit"])
