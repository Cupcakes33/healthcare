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
