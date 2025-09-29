from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def _rate_limit_key(request: Request) -> str:
    # En desarrollo/pruebas, evita colisiones entre tests generando una clave por request
    if getattr(settings, "DEBUG", False):
        return (
            request.headers.get("X-RateLimit-Key")
            or request.headers.get("X-Request-ID")
            or f"{request.client.host}-{id(request)}"
        )
    return get_remote_address(request)


# Instancia única del rate limiter para toda la app
limiter = Limiter(key_func=_rate_limit_key)


