import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models.board as _models_board  # noqa: F401
import app.models.column as _models_column  # noqa: F401
import app.models.comment as _models_comment  # noqa: F401
import app.models.task as _models_task  # noqa: F401

# Asegura el registro de modelos en Base.metadata
import app.models.user as _models_user  # noqa: F401
from app.core.cache import init_cache
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app

# Configurar una BD SQLite en memoria compartida para pruebas
test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine, future=True)

# Habilitar claves foráneas y cascadas en SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: D401
    # Activa el soporte de cascadas en SQLite
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    # Señalar entorno de pruebas para usar caché en memoria
    settings.ENV = "test"
    # Inicializar caché (InMemoryBackend en tests)
    init_cache()
    Base.metadata.create_all(bind=test_engine)
    # Override de la dependencia de BD
    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def anyio_backend():
    return "asyncio"


