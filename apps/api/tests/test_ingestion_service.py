from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Agent, Organization, Run, Span
from app.schemas.ingestion import AgentIn, IngestTraceRequest, RunIn, SpanIn, ToolCallIn
from app.services.ingestion_service import ingest_run


def _payload(**overrides: object) -> IngestTraceRequest:
    now = datetime.now(UTC)
    defaults: dict = {
        "agent": AgentIn(name="support-bot", version="1.0.0"),
        "run": RunIn(
            status="completed",
            started_at=now,
            spans=[
                SpanIn(
                    local_id="root",
                    kind="llm_call",
                    started_at=now,
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
                SpanIn(
                    local_id="child",
                    parent_local_id="root",
                    kind="tool_call",
                    started_at=now,
                    tool_calls=[ToolCallIn(tool_name="lookup_order", arguments={"id": "1"})],
                ),
            ],
        ),
    }
    defaults.update(overrides)
    return IngestTraceRequest(**defaults)


@pytest.mark.asyncio
async def test_ingest_run_creates_agent_run_and_span_hierarchy(db_session: AsyncSession) -> None:
    org = Organization(name="Acme Corp")
    db_session.add(org)
    await db_session.flush()

    run, span_count = await ingest_run(db_session, org, _payload())

    assert span_count == 2
    assert run.status == "completed"

    agent = (await db_session.execute(select(Agent))).scalar_one()
    assert agent.name == "support-bot"
    assert agent.organization_id == org.id

    spans = (
        (
            await db_session.execute(
                select(Span).where(Span.run_id == run.id).options(selectinload(Span.tool_calls))
            )
        )
        .scalars()
        .all()
    )
    assert len(spans) == 2

    root = next(s for s in spans if s.kind == "llm_call")
    child = next(s for s in spans if s.kind == "tool_call")
    assert child.parent_span_id == root.id
    assert child.tool_calls[0].tool_name == "lookup_order"


@pytest.mark.asyncio
async def test_ingest_run_reuses_existing_agent_and_updates_version(
    db_session: AsyncSession,
) -> None:
    org = Organization(name="Acme Corp")
    db_session.add(org)
    await db_session.flush()

    await ingest_run(db_session, org, _payload())
    await ingest_run(
        db_session,
        org,
        _payload(agent=AgentIn(name="support-bot", version="1.1.0")),
    )

    agents = (await db_session.execute(select(Agent))).scalars().all()
    assert len(agents) == 1
    assert agents[0].version == "1.1.0"

    runs = (await db_session.execute(select(Run))).scalars().all()
    assert len(runs) == 2


@pytest.mark.asyncio
async def test_ingest_run_with_no_spans(db_session: AsyncSession) -> None:
    org = Organization(name="Acme Corp")
    db_session.add(org)
    await db_session.flush()

    run, span_count = await ingest_run(
        db_session,
        org,
        _payload(run=RunIn(status="running", started_at=datetime.now(UTC), spans=[])),
    )

    assert span_count == 0
    assert run.status == "running"
