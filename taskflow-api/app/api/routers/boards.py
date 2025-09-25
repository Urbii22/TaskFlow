from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.board import BoardCreate, BoardRead, BoardUpdate
from app.services.board_service import (
    create_board,
    delete_board,
    get_all_boards_by_user,
    get_board,
    update_board,
)


router = APIRouter(prefix="/boards", tags=["boards"])


@router.post("/", response_model=BoardRead, status_code=status.HTTP_201_CREATED)
def create_board_endpoint(
    board_in: BoardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_board(db, current_user=current_user, board_in=board_in)


@router.get("/", response_model=list[BoardRead])
def list_boards_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_all_boards_by_user(db, current_user=current_user)


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
def update_board_endpoint(
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
def delete_board_endpoint(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    board = delete_board(db, board_id=board_id, current_user=current_user)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tablero no encontrado o sin permisos")
    return board


