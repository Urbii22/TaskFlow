import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app as fastapi_app


@pytest.mark.anyio
async def test_boards_requires_auth():
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/boards/")
    assert resp.status_code in (401, 403)


