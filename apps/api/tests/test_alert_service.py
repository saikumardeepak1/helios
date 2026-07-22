from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, Alert, Organization, Run
from app.services.dashboard_service import get_alert, list_alerts


async def _seed(
    db_session: AsyncSession, category: str, severity: str
) -> tuple[Organization, Alert]:
    org = Organization(name="Acme Corp")
    agent = Agent(name="support-bot", version="1.0.0")
    org.agents.append(agent)
    db_session.add(org)
    await db_session.flush()

    run = Run(agent_id=agent.id, status="completed", started_at=datetime.now(UTC), risk_score=80)
    db_session.add(run)
    await db_session.flush()

    alert = Alert(run_id=run.id, category=category, severity=severity, detail="test detail")
    db_session.add(alert)
    await db_session.commit()
    await db_session.refresh(alert)
    return org, alert


@pytest.mark.asyncio
async def test_list_alerts_scopes_to_organization(db_session: AsyncSession) -> None:
    org, alert = await _seed(db_session, "pii", "high")
    await _seed(db_session, "pii", "high")

    results = await list_alerts(db_session, org.id)

    assert len(results) == 1
    assert results[0].id == alert.id
    assert results[0].agent_name == "support-bot"


@pytest.mark.asyncio
async def test_list_alerts_filters_by_severity(db_session: AsyncSession) -> None:
    org, _ = await _seed(db_session, "pii", "high")
    agent = Agent(name="another-bot", version="1.0.0")
    org_result = await db_session.get(Organization, org.id)
    assert org_result is not None
    org_result.agents.append(agent)
    await db_session.flush()
    run = Run(agent_id=agent.id, status="completed", started_at=datetime.now(UTC))
    db_session.add(run)
    await db_session.flush()
    db_session.add(
        Alert(run_id=run.id, category="prompt_injection", severity="critical", detail="x")
    )
    await db_session.commit()

    high = await list_alerts(db_session, org.id, severity="high")
    critical = await list_alerts(db_session, org.id, severity="critical")

    assert len(high) == 1
    assert len(critical) == 1
    assert high[0].severity == "high"
    assert critical[0].severity == "critical"


@pytest.mark.asyncio
async def test_list_alerts_filters_by_category(db_session: AsyncSession) -> None:
    org, _ = await _seed(db_session, "pii", "high")

    pii_alerts = await list_alerts(db_session, org.id, category="pii")
    injection_alerts = await list_alerts(db_session, org.id, category="prompt_injection")

    assert len(pii_alerts) == 1
    assert injection_alerts == []


@pytest.mark.asyncio
async def test_get_alert_returns_none_for_other_organization(db_session: AsyncSession) -> None:
    _, alert = await _seed(db_session, "pii", "high")
    other_org = Organization(name="Other Org")
    db_session.add(other_org)
    await db_session.commit()

    result = await get_alert(db_session, other_org.id, alert.id)

    assert result is None


@pytest.mark.asyncio
async def test_get_alert_returns_full_detail(db_session: AsyncSession) -> None:
    org, alert = await _seed(db_session, "pii", "critical")

    result = await get_alert(db_session, org.id, alert.id)

    assert result is not None
    assert result.detail == "test detail"
    assert result.run_id == alert.run_id
