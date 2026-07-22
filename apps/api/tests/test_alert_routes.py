from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models import Agent, Alert, Organization, Run, User


async def _seed_with_session(db_session: AsyncSession) -> tuple[str, Alert]:
    org = Organization(name="Acme Corp")
    user = User(email="a@acme.com", hashed_password=hash_password("x"))
    agent = Agent(name="support-bot", version="1.0.0")
    org.users.append(user)
    org.agents.append(agent)
    db_session.add(org)
    await db_session.flush()

    run = Run(agent_id=agent.id, status="completed", started_at=datetime.now(UTC), risk_score=80)
    db_session.add(run)
    await db_session.flush()

    alert = Alert(run_id=run.id, category="pii", severity="high", detail="Detected an SSN")
    db_session.add(alert)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(alert)

    return create_access_token(str(user.id)), alert


@pytest.mark.asyncio
async def test_list_alerts_requires_session(client: AsyncClient) -> None:
    response = await client.get("/v1/alerts")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_alerts_returns_scoped_alerts(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token, alert = await _seed_with_session(db_session)

    response = await client.get("/v1/alerts", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(alert.id)
    assert body[0]["agent_name"] == "support-bot"


@pytest.mark.asyncio
async def test_get_alert_detail_returns_404_for_unknown_alert(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token, _ = await _seed_with_session(db_session)

    response = await client.get(
        "/v1/alerts/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_alert_detail_returns_alert_with_run_link(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token, alert = await _seed_with_session(db_session)

    response = await client.get(
        f"/v1/alerts/{alert.id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == str(alert.run_id)
    assert body["detail"] == "Detected an SSN"
