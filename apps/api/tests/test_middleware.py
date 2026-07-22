import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_response_includes_a_generated_request_id(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


@pytest.mark.asyncio
async def test_response_echoes_a_caller_supplied_request_id(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-ID": "caller-supplied-id"})
    assert response.headers["X-Request-ID"] == "caller-supplied-id"


@pytest.mark.asyncio
async def test_each_request_without_an_id_gets_a_different_one(client: AsyncClient) -> None:
    first = await client.get("/health")
    second = await client.get("/health")
    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]
