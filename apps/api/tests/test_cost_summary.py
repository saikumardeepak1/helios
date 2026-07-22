from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, CostRecord, Organization, Run
from app.services.dashboard_service import get_cost_summary


async def _seed(db_session: AsyncSession, started_at: datetime, cost: Decimal) -> Organization:
    org = Organization(name="Acme Corp")
    agent = Agent(name="support-bot", version="1.0.0")
    org.agents.append(agent)
    db_session.add(org)
    await db_session.flush()

    run = Run(agent_id=agent.id, status="completed", started_at=started_at)
    db_session.add(run)
    await db_session.flush()

    db_session.add(CostRecord(run_id=run.id, model="gpt-4o-mini", cost_usd=cost))
    await db_session.commit()
    return org


@pytest.mark.asyncio
async def test_cost_summary_totals_and_groups_by_agent(db_session: AsyncSession) -> None:
    org = await _seed(db_session, datetime.now(UTC), Decimal("1.50"))

    summary = await get_cost_summary(db_session, org.id)

    assert summary.total_usd == Decimal("1.50")
    assert len(summary.by_agent) == 1
    assert summary.by_agent[0].agent_name == "support-bot"
    assert summary.by_agent[0].cost_usd == Decimal("1.50")
    assert len(summary.by_day) == 1


@pytest.mark.asyncio
async def test_cost_summary_excludes_costs_outside_the_window(db_session: AsyncSession) -> None:
    org = await _seed(
        db_session, datetime.now(UTC) - timedelta(days=60), Decimal("5.00")
    )

    summary = await get_cost_summary(db_session, org.id, days=30)

    assert summary.total_usd == Decimal("0")
    assert summary.by_agent == []


@pytest.mark.asyncio
async def test_cost_summary_scopes_to_organization(db_session: AsyncSession) -> None:
    await _seed(db_session, datetime.now(UTC), Decimal("2.00"))
    other_org = Organization(name="Other Org")
    db_session.add(other_org)
    await db_session.commit()

    summary = await get_cost_summary(db_session, other_org.id)

    assert summary.total_usd == Decimal("0")
