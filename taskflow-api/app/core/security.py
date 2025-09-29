from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Configuración de passlib para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que el hash corresponda a la contraseña en texto plano."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña."""
    return pwd_context.hash(password)


# Algoritmo JWT
ALGORITHM = "HS256"


def create_access_token(data: Dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Crea un JWT firmado con fecha de expiración.

    data: payload a incluir en el token (por ejemplo, {"sub": email}).
    expires_delta: delta de expiración; si no se provee, usa settings.ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    to_encode = data.copy()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
