from typing import Callable

import anyio
import redis.asyncio as redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.coder import JsonCoder

from app.core.config import settings


def init_cache() -> None:
    """Inicializa FastAPICache con backend de Redis.

    Usa la URL definida en settings.REDIS_URL.
    """
    # En pruebas usamos backend en memoria para no depender de Redis
    if settings.ENV.lower().startswith("test"):
        FastAPICache.init(InMemoryBackend(), prefix="taskflow-cache:", coder=JsonCoder())
    else:
        # Importante: no usar decode_responses=True porque fastapi-cache
        # espera bytes y realiza value.decode() durante la deserialización.
        # Si Redis devuelve str se produce: 'str' object has no attribute 'decode'.
        redis_client = redis.from_url(settings.REDIS_URL)
        FastAPICache.init(RedisBackend(redis_client), prefix="taskflow-cache:", coder=JsonCoder())


def default_key_builder(func: Callable, namespace: str = "", request=None, response=None, *args, **kwargs) -> str:
    """Creador de claves por defecto que incluye usuario autenticado cuando existe.

    Así evitamos mezclar respuestas entre usuarios.
    """
    parts: list[str] = [namespace or func.__module__ + ":" + func.__name__]
    if request is not None:
        # Incluir path y query
        parts.append(request.url.path)
        if request.url.query:
            parts.append("?" + request.url.query)
        # Incluir user id si está disponible
        try:
            user = request.state.user if hasattr(request.state, "user") else None
            if user and getattr(user, "id", None) is not None:
                parts.append(f"|u:{user.id}")
        except Exception:
            pass
    return "".join(parts)


async def _clear_namespaces(namespaces: list[str]) -> None:
    for ns in namespaces:
        try:
            await FastAPICache.clear(namespace=ns)
        except Exception:
            # Evitar que la invalidación rompa la petición principal
            pass


def invalidate_tasks_cache_for_user(_: int) -> None:
    """Invalidación gruesa por espacios de nombres para tareas.

    Por simplicidad y robustez (y TTL corto), limpiamos los espacios
    de nombres de tareas en cambios (create/update/delete).
    """
    try:
        anyio.from_thread.run(_clear_namespaces, ["tasks:get", "tasks:search"])
    except Exception:
        # Si no hay loop (tests sync), intentamos crear uno
        try:
            import asyncio

            asyncio.run(_clear_namespaces(["tasks:get", "tasks:search"]))
        except Exception:
            pass
