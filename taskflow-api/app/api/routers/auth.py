from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import create_user
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token
from app.schemas.token import Token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    try:
        user = create_user(db, user_in=user_in)
        return user
    except ValueError as e:
        # Email duplicado u otras validaciones del dominio
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    # username vendrá como email
    user_repo = UserRepository()
    user = user_repo.get_by_email(db, email=form_data.username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credenciales inválidas")

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credenciales inválidas")

    access_token = create_access_token({"sub": user.email})
    return Token(access_token=access_token, token_type="bearer")


