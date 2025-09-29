import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app as fastapi_app
from app.schemas.task import TaskCreate
from fastapi_cache import FastAPICache


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
        data_page = resp_list.json()
        assert any(b["id"] == board["id"] for b in data_page["items"])

        # Segunda llamada debería salir de caché sin error
        resp_list_cached = await ac.get("/api/v1/boards/", headers=headers_a)
        assert resp_list_cached.status_code == 200

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


@pytest.mark.anyio
async def test_tasks_api_crud_and_permissions():
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token_a = await register_and_login(ac, "taskapia@example.com", "secret123")
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Crear board y columna
        board = (await ac.post("/api/v1/boards/", json={"name": "B"}, headers=headers_a)).json()
        column = (
            await ac.post(
                "/api/v1/columns/",
                json={"name": "C1", "position": 1, "board_id": board["id"]},
                headers=headers_a,
            )
        ).json()

        # Crear tarea
        resp_task = await ac.post(
            "/api/v1/tasks/",
            json={"title": "T1", "description": "d", "priority": "MEDIUM", "column_id": column["id"]},
            headers=headers_a,
        )
        assert resp_task.status_code == 201, resp_task.text
        task = resp_task.json()

        # Obtener y listar
        assert (await ac.get(f"/api/v1/tasks/{task['id']}", headers=headers_a)).status_code == 200
        resp_list = await ac.get(f"/api/v1/columns/{column['id']}/tasks", headers=headers_a)
        assert resp_list.status_code == 200
        data_tasks = resp_list.json()
        assert any(t["id"] == task["id"] for t in data_tasks["items"])

        # Crear otra tarea con distinta prioridad y assignee
        resp_task2 = await ac.post(
            "/api/v1/tasks/",
            json={
                "title": "T2",
                "description": None,
                "priority": "HIGH",
                "column_id": column["id"],
            },
            headers=headers_a,
        )
        assert resp_task2.status_code == 201, resp_task2.text
        task2 = resp_task2.json()

        # Filtrar por prioridad HIGH
        resp_filter_prio = await ac.get(
            f"/api/v1/columns/{column['id']}/tasks?priority=HIGH",
            headers=headers_a,
        )
        assert resp_filter_prio.status_code == 200
        tasks_high_page = resp_filter_prio.json()
        assert all(t["priority"] == "HIGH" for t in tasks_high_page["items"])
        assert any(t["id"] == task2["id"] for t in tasks_high_page["items"])

        # Asignar task1 al usuario (PUT/PATCH de tarea)
        resp_assign = await ac.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"assignee_id": 1},
            headers=headers_a,
        )
        assert resp_assign.status_code == 200

        # Filtrar por assignee_id
        resp_filter_assignee = await ac.get(
            f"/api/v1/columns/{column['id']}/tasks?assignee_id=1",
            headers=headers_a,
        )
        assert resp_filter_assignee.status_code == 200
        tasks_assignee_page = resp_filter_assignee.json()
        assert any(t["id"] == task["id"] for t in tasks_assignee_page["items"])

        # Actualizar
        resp_upd = await ac.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"title": "T2", "priority": "HIGH"},
            headers=headers_a,
        )
        assert resp_upd.status_code == 200 and resp_upd.json()["title"] == "T2"

        # Búsqueda y caché
        resp_search = await ac.get("/api/v1/tasks/?q=T2", headers=headers_a)
        assert resp_search.status_code == 200
        resp_search_cached = await ac.get("/api/v1/tasks/?q=T2", headers=headers_a)
        assert resp_search_cached.status_code == 200

        # Usuario B no puede acceder
        token_b = await register_and_login(ac, "taskapib@example.com", "secret123")
        headers_b = {"Authorization": f"Bearer {token_b}"}
        assert (await ac.get(f"/api/v1/tasks/{task['id']}", headers=headers_b)).status_code == 404
        assert (
            await ac.patch(f"/api/v1/tasks/{task['id']}", json={"title": "X"}, headers=headers_b)
        ).status_code == 404
        assert (await ac.delete(f"/api/v1/tasks/{task['id']}", headers=headers_b)).status_code == 404

        # Eliminar (A)
        assert (await ac.delete(f"/api/v1/tasks/{task['id']}", headers=headers_a)).status_code == 200



