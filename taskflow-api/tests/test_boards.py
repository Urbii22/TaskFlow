import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app as fastapi_app


async def register_and_login(ac: AsyncClient, email: str, password: str) -> str:
    resp_reg = await ac.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert resp_reg.status_code == 201, resp_reg.text
    resp_login = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp_login.status_code == 200, resp_login.text
    return resp_login.json()["access_token"]


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_boards_crud_and_ownership():
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token_a = await register_and_login(ac, "boardusera@example.com", "secret123")
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Crear board
        resp_create = await ac.post("/api/v1/boards/", json={"name": "Board A"}, headers=headers_a)
        assert resp_create.status_code == 201, resp_create.text
        board = resp_create.json()

        # Listar mis boards
        resp_list = await ac.get("/api/v1/boards/", headers=headers_a)
        assert resp_list.status_code == 200
        assert any(b["id"] == board["id"] for b in resp_list.json())

        # Obtener board
        resp_get = await ac.get(f"/api/v1/boards/{board['id']}", headers=headers_a)
        assert resp_get.status_code == 200

        # Actualizar board
        resp_update = await ac.patch(f"/api/v1/boards/{board['id']}", json={"name": "Board A2"}, headers=headers_a)
        assert resp_update.status_code == 200
        assert resp_update.json()["name"] == "Board A2"

        # Otro usuario
        token_b = await register_and_login(ac, "boarduserb@example.com", "secret123")
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # B no puede ver/editar/eliminar board de A
        assert (await ac.get(f"/api/v1/boards/{board['id']}", headers=headers_b)).status_code == 404
        assert (
            await ac.patch(f"/api/v1/boards/{board['id']}", json={"name": "X"}, headers=headers_b)
        ).status_code == 404
        assert (await ac.delete(f"/api/v1/boards/{board['id']}", headers=headers_b)).status_code == 404

        # Eliminar board (A)
        resp_delete = await ac.delete(f"/api/v1/boards/{board['id']}", headers=headers_a)
        assert resp_delete.status_code == 200


