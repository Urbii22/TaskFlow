from fastapi import Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from fastapi import Request


# Esquema OAuth2 para extraer el token Bearer del encabezado Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    request: Request = None,
) -> User:
    """Obtiene el usuario actual a partir del JWT.

    - Decodifica el token para extraer el email (sub)
    - Maneja tokens inválidos o expirados
    - Busca y retorna el usuario completo de la base de datos
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        email: str = str(subject)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token ha expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception

    user_repo = UserRepository()
    user = user_repo.get_by_email(db, email=email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    # Guardamos el usuario en request.state para key-builder de caché
    try:
        if request is not None:
            request.state.user = user
    except Exception:
        pass
    return user


def get_pagination_params(
    skip: int = Query(0, ge=0, description="Número de elementos a saltar (offset)"),
    limit: int = Query(100, ge=1, le=1000, description="Tamaño de página (límite de elementos)"),
):
    return {"skip": skip, "limit": limit}

