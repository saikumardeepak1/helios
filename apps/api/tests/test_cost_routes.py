from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models import Agent, CostRecord, Organization, Run, User


@pytest.mark.asyncio
async def test_cost_summary_requires_session(client: AsyncClient) -> None:
    response = await client.get("/v1/cost/summary")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cost_summary_returns_totals(client: AsyncClient, db_session: AsyncSession) -> None:
    org = Organization(name="Acme Corp")
    user = User(email="a@acme.com", hashed_password=hash_password("x"))
    agent = Agent(name="support-bot", version="1.0.0")
    org.users.append(user)
    org.agents.append(agent)
    db_session.add(org)
    await db_session.flush()

    run = Run(agent_id=agent.id, status="completed", started_at=datetime.now(UTC))
    db_session.add(run)
    await db_session.flush()
    db_session.add(CostRecord(run_id=run.id, model="gpt-4o-mini", cost_usd=Decimal("0.42")))
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(str(user.id))
    response = await client.get("/v1/cost/summary", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert Decimal(body["total_usd"]) == Decimal("0.42")
    assert body["by_agent"][0]["agent_name"] == "support-bot"
