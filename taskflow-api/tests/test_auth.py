import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.db.base import Base
from app.db.session import get_db
import app.models.user as _models_user  # asegura el registro de modelos en Base.metadata
import app.models.board as _models_board
import app.models.task as _models_task
import app.models.comment as _models_comment
import app.models.column as _models_column


# Configurar una BD SQLite en memoria compartida para pruebas
test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine, future=True)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    Base.metadata.create_all(bind=test_engine)
    # Override de la dependencia de BD
    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_register_success():
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {"email": "user@example.com", "password": "secret123"}
        resp = await ac.post("/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["email"] == "user@example.com"
    assert "id" in data and isinstance(data["id"], int)
    assert data["role"] == "USER"


@pytest.mark.anyio
async def test_register_duplicate_email():
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {"email": "dup@example.com", "password": "secret123"}
        first = await ac.post("/auth/register", json=payload)
        assert first.status_code == 201
        second = await ac.post("/auth/register", json=payload)
    assert second.status_code == 400
    assert "Email ya registrado" in second.text


@pytest.mark.anyio
async def test_login_success():
    email = "login@example.com"
    password = "secret123"
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # registrar usuario
        resp = await ac.post("/auth/register", json={"email": email, "password": password})
        assert resp.status_code == 201
        # login
        form = {"username": email, "password": password}
        resp_login = await ac.post("/auth/login", data=form)
    assert resp_login.status_code == 200, resp_login.text
    token = resp_login.json()
    assert "access_token" in token and isinstance(token["access_token"], str)
    assert token["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_wrong_password():
    email = "wrongpass@example.com"
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # registrar usuario
        resp = await ac.post("/auth/register", json={"email": email, "password": "correct"})
        assert resp.status_code == 201
        # login con contraseña errónea
        resp_login = await ac.post("/auth/login", data={"username": email, "password": "incorrect"})
    assert resp_login.status_code == 400
    assert "Credenciales inválidas" in resp_login.text


