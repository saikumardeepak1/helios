from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, Organization, Run, Span, ToolCall
from app.services.dashboard_service import get_run_detail, list_runs


async def _seed(db_session: AsyncSession) -> tuple[Organization, Agent, Run]:
    org = Organization(name="Acme Corp")
    agent = Agent(name="support-bot", version="1.0.0")
    org.agents.append(agent)
    db_session.add(org)
    await db_session.flush()

    run = Run(agent_id=agent.id, status="completed", started_at=datetime.now(UTC))
    db_session.add(run)
    await db_session.flush()

    span = Span(run_id=run.id, kind="llm_call", started_at=datetime.now(UTC), prompt_tokens=5)
    db_session.add(span)
    await db_session.flush()

    db_session.add(ToolCall(span_id=span.id, tool_name="lookup_order", result={"ok": True}))
    await db_session.commit()

    return org, agent, run


@pytest.mark.asyncio
async def test_list_runs_scopes_to_organization_and_includes_span_count(
    db_session: AsyncSession,
) -> None:
    org, _, run = await _seed(db_session)
    other_org, other_agent, _ = await _seed(db_session)

    results = await list_runs(db_session, org.id)

    assert len(results) == 1
    assert results[0].id == run.id
    assert results[0].agent_name == "support-bot"
    assert results[0].span_count == 1


@pytest.mark.asyncio
async def test_list_runs_filters_by_status(db_session: AsyncSession) -> None:
    org, agent, _ = await _seed(db_session)
    db_session.add(Run(agent_id=agent.id, status="failed", started_at=datetime.now(UTC)))
    await db_session.commit()

    completed = await list_runs(db_session, org.id, status="completed")
    failed = await list_runs(db_session, org.id, status="failed")

    assert len(completed) == 1
    assert len(failed) == 1
    assert completed[0].status == "completed"
    assert failed[0].status == "failed"


@pytest.mark.asyncio
async def test_get_run_detail_includes_spans_and_tool_calls(db_session: AsyncSession) -> None:
    org, _, run = await _seed(db_session)

    detail = await get_run_detail(db_session, org.id, run.id)

    assert detail is not None
    assert detail.agent_name == "support-bot"
    assert len(detail.spans) == 1
    assert detail.spans[0].tool_calls[0].tool_name == "lookup_order"


@pytest.mark.asyncio
async def test_get_run_detail_returns_none_for_other_organization(
    db_session: AsyncSession,
) -> None:
    _, _, run = await _seed(db_session)
    other_org = Organization(name="Other Org")
    db_session.add(other_org)
    await db_session.commit()

    detail = await get_run_detail(db_session, other_org.id, run.id)

    assert detail is None
