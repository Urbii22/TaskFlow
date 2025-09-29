import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app as fastapi_app


@pytest.mark.anyio
async def test_register_success():
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {"email": "user@example.com", "password": "secret123"}
        resp = await ac.post("/api/v1/auth/register", json=payload)
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
        first = await ac.post("/api/v1/auth/register", json=payload)
        assert first.status_code == 201
        second = await ac.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 400
    assert "Email ya registrado" in second.text


@pytest.mark.anyio
async def test_login_success():
    email = "login@example.com"
    password = "secret123"
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # registrar usuario
        resp = await ac.post("/api/v1/auth/register", json={"email": email, "password": password})
        assert resp.status_code == 201
        # login
        form = {"username": email, "password": password}
        resp_login = await ac.post("/api/v1/auth/login", data=form)
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
        resp = await ac.post("/api/v1/auth/register", json={"email": email, "password": "correct"})
        assert resp.status_code == 201
        # login con contraseña errónea
        resp_login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "incorrect"})
    assert resp_login.status_code == 400
    assert "Credenciales inválidas" in resp_login.text


