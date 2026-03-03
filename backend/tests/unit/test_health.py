import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness(client: AsyncClient) -> None:
    """Health endpoint should return 200 with status ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
