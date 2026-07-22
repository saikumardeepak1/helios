from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Agent, Alert, ApiKey, CostRecord, Organization, Run, Span, ToolCall, User


@pytest.mark.asyncio
async def test_organization_cascades_to_users_and_agents(db_session: AsyncSession) -> None:
    org = Organization(name="Acme Corp")
    org.users.append(User(email="a@acme.com", hashed_password="x", role="admin"))
    org.agents.append(Agent(name="support-bot", version="1.0.0"))
    db_session.add(org)
    await db_session.commit()

    fetched = (await db_session.execute(select(Organization))).scalar_one()
    assert len(fetched.users) == 1
    assert len(fetched.agents) == 1

    await db_session.delete(fetched)
    await db_session.commit()

    assert (await db_session.execute(select(User))).scalars().all() == []
    assert (await db_session.execute(select(Agent))).scalars().all() == []


@pytest.mark.asyncio
async def test_api_key_belongs_to_organization(db_session: AsyncSession) -> None:
    org = Organization(name="Acme Corp")
    key = ApiKey(prefix="hel_live", hashed_key="hashed")
    org.api_keys.append(key)
    db_session.add(org)
    await db_session.commit()

    fetched = (await db_session.execute(select(ApiKey))).scalar_one()
    assert fetched.organization.name == "Acme Corp"
    assert fetched.revoked_at is None


@pytest.mark.asyncio
async def test_run_span_hierarchy_and_tool_calls(db_session: AsyncSession) -> None:
    org = Organization(name="Acme Corp")
    agent = Agent(name="support-bot", version="1.0.0")
    org.agents.append(agent)
    db_session.add(org)
    await db_session.flush()

    run = Run(agent_id=agent.id, status="running", started_at=datetime.now(UTC))
    db_session.add(run)
    await db_session.flush()

    parent_span = Span(
        run_id=run.id, kind="llm_call", started_at=datetime.now(UTC), prompt_tokens=10
    )
    db_session.add(parent_span)
    await db_session.flush()

    child_span = Span(
        run_id=run.id,
        parent_span_id=parent_span.id,
        kind="tool_call",
        started_at=datetime.now(UTC),
    )
    db_session.add(child_span)
    await db_session.flush()

    tool_call = ToolCall(
        span_id=child_span.id,
        tool_name="lookup_order",
        arguments={"order_id": "123"},
        result={"status": "shipped"},
    )
    db_session.add(tool_call)
    await db_session.commit()

    fetched_run = (
        await db_session.execute(select(Run).options(selectinload(Run.spans)))
    ).scalar_one()
    assert len(fetched_run.spans) == 2

    fetched_parent = (
        await db_session.execute(
            select(Span)
            .where(Span.id == parent_span.id)
            .options(selectinload(Span.children).selectinload(Span.tool_calls))
        )
    ).scalar_one()
    assert len(fetched_parent.children) == 1
    assert fetched_parent.children[0].tool_calls[0].tool_name == "lookup_order"


@pytest.mark.asyncio
async def test_cost_record_and_alert_attach_to_run(db_session: AsyncSession) -> None:
    org = Organization(name="Acme Corp")
    agent = Agent(name="support-bot", version="1.0.0")
    org.agents.append(agent)
    db_session.add(org)
    await db_session.flush()

    run = Run(agent_id=agent.id, status="completed", started_at=datetime.now(UTC))
    db_session.add(run)
    await db_session.flush()

    db_session.add(CostRecord(run_id=run.id, model="gpt-4o", cost_usd=Decimal("0.0123")))
    db_session.add(
        Alert(
            run_id=run.id,
            category="pii",
            severity="high",
            detail="Detected an email address in output",
        )
    )
    await db_session.commit()

    fetched_run = (
        await db_session.execute(
            select(Run).options(selectinload(Run.cost_records), selectinload(Run.alerts))
        )
    ).scalar_one()
    assert fetched_run.cost_records[0].cost_usd == Decimal("0.0123")
    assert fetched_run.alerts[0].severity == "high"


@pytest.mark.asyncio
async def test_user_email_is_unique(db_session: AsyncSession) -> None:
    org = Organization(name="Acme Corp")
    org.users.append(User(email="dup@acme.com", hashed_password="x"))
    org.users.append(User(email="dup@acme.com", hashed_password="y"))
    db_session.add(org)

    with pytest.raises(Exception):  # noqa: B017 - asserting a DB integrity error, driver-specific
        await db_session.commit()
