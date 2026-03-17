import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    # given
    transport = ASGITransport(app=app)

    # when
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    # then
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_v1_root():
    # given
    transport = ASGITransport(app=app)

    # when
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/")

    # then
    assert response.status_code == 200
    assert response.json() == {"message": "API v1"}


@pytest.mark.asyncio
async def test_cors_headers():
    # given
    transport = ASGITransport(app=app)
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    }

    # when
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options("/health", headers=headers)

    # then
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


@pytest.mark.asyncio
async def test_404_error_format():
    # given
    transport = ASGITransport(app=app)

    # when
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/nonexistent")

    # then
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "HTTP_404"


@pytest.mark.asyncio
async def test_config_defaults():
    # given / when
    from app.core.config import settings

    # then
    assert settings.ADMIN_USERNAME == "admin"
    assert settings.LLM_PROVIDER == "openai"
    assert "http://localhost:3000" in settings.cors_origins_list
    assert settings.CHAT_MODEL == "gpt-4.1-nano"
    assert settings.ANALYSIS_MODEL == "gpt-4.1"
