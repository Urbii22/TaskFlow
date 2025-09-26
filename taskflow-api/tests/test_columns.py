import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app as fastapi_app


async def register_and_login(ac: AsyncClient, email: str, password: str) -> str:
    resp_reg = await ac.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert resp_reg.status_code == 201, resp_reg.text
    resp_login = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp_login.status_code == 200, resp_login.text
    token = resp_login.json()["access_token"]
    return token


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_columns_crud_and_security():
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Usuario A
        token_a = await register_and_login(ac, "usera@example.com", "secret123")
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Crear board A
        resp_board_a = await ac.post("/api/v1/boards/", json={"name": "Board A"}, headers=headers_a)
        assert resp_board_a.status_code == 201, resp_board_a.text
        board_a = resp_board_a.json()

        # Crear columna en board A
        payload_col = {"name": "To Do", "position": 1, "board_id": board_a["id"]}
        resp_create_col = await ac.post("/api/v1/columns/", json=payload_col, headers=headers_a)
        assert resp_create_col.status_code == 201, resp_create_col.text
        column = resp_create_col.json()
        assert column["name"] == "To Do"
        assert column["board_id"] == board_a["id"]

        # Obtener columna
        resp_get_col = await ac.get(f"/api/v1/columns/{column['id']}", headers=headers_a)
        assert resp_get_col.status_code == 200

        # Listar columnas del board
        resp_list_cols = await ac.get(f"/api/v1/boards/{board_a['id']}/columns", headers=headers_a)
        assert resp_list_cols.status_code == 200
        cols = resp_list_cols.json()
        assert isinstance(cols, list) and len(cols) == 1

        # Actualizar columna
        resp_update_col = await ac.patch(
            f"/api/v1/columns/{column['id']}", json={"name": "Backlog", "position": 2}, headers=headers_a
        )
        assert resp_update_col.status_code == 200
        updated = resp_update_col.json()
        assert updated["name"] == "Backlog" and updated["position"] == 2

        # Usuario B (otro dueño)
        token_b = await register_and_login(ac, "userb@example.com", "secret123")
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # Intentar crear columna en board de A desde B -> 404 por ownership
        resp_create_forbidden = await ac.post(
            "/api/v1/columns/", json={"name": "X", "position": 1, "board_id": board_a["id"]}, headers=headers_b
        )
        assert resp_create_forbidden.status_code == 404

        # Intentar leer columna de A desde B -> 404 por ownership
        resp_get_forbidden = await ac.get(f"/api/v1/columns/{column['id']}", headers=headers_b)
        assert resp_get_forbidden.status_code == 404

        # Intentar listar columnas del board A desde B -> 404 por ownership
        resp_list_forbidden = await ac.get(f"/api/v1/boards/{board_a['id']}/columns", headers=headers_b)
        assert resp_list_forbidden.status_code == 404

        # Eliminar columna (dueño A)
        resp_delete_col = await ac.delete(f"/api/v1/columns/{column['id']}", headers=headers_a)
        assert resp_delete_col.status_code == 200


@pytest.mark.anyio
async def test_columns_requires_auth_and_not_found_cases():
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Sin token -> 401
        resp_unauth = await ac.post("/api/v1/columns/", json={"name": "N", "position": 1, "board_id": 1})
        assert resp_unauth.status_code in (401, 403)

        # Usuario A
        token_a = await register_and_login(ac, "userc@example.com", "secret123")
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Board inexistente -> 404 al crear
        resp_create_404 = await ac.post(
            "/api/v1/columns/", json={"name": "N", "position": 1, "board_id": 9999}, headers=headers_a
        )
        assert resp_create_404.status_code == 404

        # Crear board y columna válida
        resp_board = await ac.post("/api/v1/boards/", json={"name": "B"}, headers=headers_a)
        assert resp_board.status_code == 201
        board = resp_board.json()
        resp_col = await ac.post(
            "/api/v1/columns/", json={"name": "C1", "position": 1, "board_id": board["id"]}, headers=headers_a
        )
        assert resp_col.status_code == 201
        col = resp_col.json()

        # PATCH vacío -> retorna recurso sin cambios (200)
        resp_patch_empty = await ac.patch(f"/api/v1/columns/{col['id']}", json={}, headers=headers_a)
        assert resp_patch_empty.status_code == 200

        # GET columna inexistente -> 404
        resp_get_404 = await ac.get("/api/v1/columns/999999", headers=headers_a)
        assert resp_get_404.status_code == 404

        # Listar columnas de board inexistente -> 404
        resp_list_404 = await ac.get("/api/v1/boards/999999/columns", headers=headers_a)
        assert resp_list_404.status_code == 404


