from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate
from app.services.comment_service import (
    create_comment,
    delete_comment,
    get_comment,
    update_comment,
)


router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def create_comment_endpoint(
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = create_comment(db, current_user=current_user, comment_in=comment_in)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada o sin permisos")
    return comment


@router.get("/{comment_id}", response_model=CommentRead)
def get_comment_endpoint(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = get_comment(db, comment_id=comment_id, current_user=current_user)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentario no encontrado o sin permisos")
    return comment


@router.patch("/{comment_id}", response_model=CommentRead)
def update_comment_endpoint(
    comment_id: int,
    comment_in: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = update_comment(db, comment_id=comment_id, comment_in=comment_in, current_user=current_user)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentario no encontrado o sin permisos")
    return comment


@router.delete("/{comment_id}", response_model=CommentRead)
def delete_comment_endpoint(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = delete_comment(db, comment_id=comment_id, current_user=current_user)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentario no encontrado o sin permisos")
    return comment


