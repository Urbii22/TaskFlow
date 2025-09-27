from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from asgi_correlation_id import CorrelationIdMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.logging import setup_logging
from app.api.routers import health as health_router
from app.api.routers import auth as auth_router
from app.api.routers import boards as boards_router
from app.api.routers import columns as columns_router
from app.api.routers import tasks as tasks_router

setup_logging()

limiter = Limiter(key_func=get_remote_address)

def create_app() -> FastAPI:
    app = FastAPI(title="TaskFlow API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationIdMiddleware)

    @app.middleware("http")
    async def add_correlation_id_header(request: Request, call_next):
        response = await call_next(request)
        # middleware ya añade X-Request-ID; lo exponemos:
        response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", "")
        return response

    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    app.state.limiter = limiter

    app.include_router(health_router.router, prefix="/api/v1", tags=["health"])
    app.include_router(auth_router.router, prefix="/api/v1")
    app.include_router(boards_router.router, prefix="/api/v1")
    app.include_router(columns_router.router, prefix="/api/v1")
    app.include_router(tasks_router.router, prefix="/api/v1")

    @app.get("/")
    def root():
        return {"app": "taskflow", "message": "OK"}

    return app

app = create_app()
