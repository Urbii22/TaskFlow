import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app as fastapi_app


@pytest.mark.anyio
async def test_root_ok_and_request_id_header_echo():
    transport = ASGITransport(app=fastapi_app)
    headers = {"X-Request-ID": "test-corr-id-123"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        resp = await ac.get("/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data.get("app") == "taskflow"
    assert data.get("message") == "OK"
    # El middleware expone el header de correlación que venga en la request
    req_id = resp.headers.get("X-Request-ID")
    assert isinstance(req_id, str) and len(req_id) > 0


@pytest.mark.anyio
async def test_metrics_endpoint_exposes_prometheus_metrics():
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    # Formato de Prometheus debe contener comentarios HELP/TYPE
    assert "# HELP" in body
    # Debe contener algún métrico HTTP instrumentado
    assert "http" in body


