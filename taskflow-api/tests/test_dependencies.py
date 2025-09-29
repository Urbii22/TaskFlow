from datetime import timedelta

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user
from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app as fastapi_app


def _get_db_session_for_test():
    gen = fastapi_app.dependency_overrides[get_db]()
    db = next(gen)
    return db, gen


@pytest.mark.anyio
async def test_get_current_user_valid_token():
    transport = ASGITransport(app=fastapi_app)
    email = "depuser@example.com"
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/auth/register", json={"email": email, "password": "secret123"})
        assert resp.status_code == 201
    token = create_access_token({"sub": email})
    db, gen = _get_db_session_for_test()
    try:
        user = get_current_user(token=token, db=db)
    finally:
        gen.close()
    assert user.email == email


def test_get_current_user_invalid_token_raises_401():
    db, gen = _get_db_session_for_test()
    try:
        with pytest.raises(HTTPException) as exc:
            _ = get_current_user(token="invalid.token.value", db=db)
    finally:
        gen.close()
    assert exc.value.status_code == 401


def test_get_current_user_expired_token_raises_401():
    email = "expired@example.com"
    # Crear usuario por la API para persistir en la BD de pruebas
    # (el registro se hace de forma síncrona usando cliente async en otra prueba; aquí basta el token)
    db, gen = _get_db_session_for_test()
    gen.close()  # no necesitamos DB para crear el token expirado

    token = create_access_token({"sub": email}, expires_delta=timedelta(seconds=-1))
    db, gen = _get_db_session_for_test()
    try:
        with pytest.raises(HTTPException) as exc:
            _ = get_current_user(token=token, db=db)
    finally:
        gen.close()
    assert exc.value.status_code == 401
