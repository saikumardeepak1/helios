from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models import Agent, Organization, Run, User


async def _seed_with_session(db_session: AsyncSession) -> tuple[str, Run]:
    org = Organization(name="Acme Corp")
    user = User(email="a@acme.com", hashed_password=hash_password("x"))
    agent = Agent(name="support-bot", version="1.0.0")
    org.users.append(user)
    org.agents.append(agent)
    db_session.add(org)
    await db_session.flush()

    run = Run(agent_id=agent.id, status="completed", started_at=datetime.now(UTC))
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(user)

    return create_access_token(str(user.id)), run


@pytest.mark.asyncio
async def test_list_runs_requires_session(client: AsyncClient) -> None:
    response = await client.get("/v1/runs")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_runs_returns_scoped_runs(client: AsyncClient, db_session: AsyncSession) -> None:
    token, run = await _seed_with_session(db_session)

    response = await client.get("/v1/runs", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(run.id)
    assert body[0]["agent_name"] == "support-bot"


@pytest.mark.asyncio
async def test_get_run_detail_returns_404_for_unknown_run(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token, _ = await _seed_with_session(db_session)

    response = await client.get(
        "/v1/runs/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_run_detail_returns_run_with_spans(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token, run = await _seed_with_session(db_session)

    response = await client.get(
        f"/v1/runs/{run.id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(run.id)
    assert body["spans"] == []
