from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.schemas.comment import CommentCreate, CommentUpdate
from app.services.task_service import get_task

comment_repository = CommentRepository()


def create_comment(
    db: Session, *, current_user: User, comment_in: CommentCreate
) -> Comment | None:
    # Validar acceso a la tarea (ser dueño del tablero)
    task = get_task(db, task_id=comment_in.task_id, current_user=current_user)
    if task is None:
        return None

    data = {
        "text": comment_in.text,
        "task_id": comment_in.task_id,
        # Forzamos el autor al usuario actual, ignorando lo recibido
        "author_id": current_user.id,
    }
    return comment_repository.create(db, data)


def get_comment(db: Session, *, comment_id: int, current_user: User) -> Comment | None:
    comment = comment_repository.get(db, comment_id)
    if comment is None:
        return None

    # Permitir si es el autor o si es dueño del tablero de la tarea
    if comment.author_id == current_user.id:
        return comment

    task = get_task(db, task_id=comment.task_id, current_user=current_user)
    if task is None:
        return None
    return comment


def update_comment(
    db: Session, *, comment_id: int, comment_in: CommentUpdate, current_user: User
) -> Comment | None:
    comment = comment_repository.get(db, comment_id)
    if comment is None:
        return None

    # Solo el autor puede editar
    if comment.author_id != current_user.id:
        return None

    update_data: dict = {}
    if comment_in.text is not None:
        update_data["text"] = comment_in.text

    if not update_data:
        return comment

    return comment_repository.update(db, comment, update_data)


def delete_comment(db: Session, *, comment_id: int, current_user: User) -> Comment | None:
    comment = comment_repository.get(db, comment_id)
    if comment is None:
        return None

    # Solo el autor puede eliminar
    if comment.author_id != current_user.id:
        return None

    return comment_repository.remove(db, comment_id)


