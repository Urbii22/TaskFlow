from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


user_repository = UserRepository()


def create_user(db: Session, *, user_in: UserCreate) -> User:
    existing = user_repository.get_by_email(db, email=user_in.email)
    if existing is not None:
        raise ValueError("Email ya registrado")

    user_data = {
        "email": user_in.email,
        "password_hash": get_password_hash(user_in.password),
    }
    return user_repository.create(db, user_data)


