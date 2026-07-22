import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Agent, Run, Span
from app.schemas.dashboard import RunDetailOut, RunSummaryOut, SpanOut


async def list_runs(
    db: AsyncSession,
    organization_id: uuid.UUID,
    status: str | None = None,
    agent_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[RunSummaryOut]:
    query = (
        select(Run, Agent.name, func.count(Span.id))
        .join(Agent, Agent.id == Run.agent_id)
        .outerjoin(Span, Span.run_id == Run.id)
        .where(Agent.organization_id == organization_id)
        .group_by(Run.id, Agent.name)
        .order_by(Run.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status is not None:
        query = query.where(Run.status == status)
    if agent_id is not None:
        query = query.where(Run.agent_id == agent_id)

    rows = (await db.execute(query)).all()

    return [
        RunSummaryOut(
            id=run.id,
            agent_name=agent_name,
            status=run.status,
            started_at=run.started_at,
            ended_at=run.ended_at,
            span_count=span_count,
            risk_score=run.risk_score,
        )
        for run, agent_name, span_count in rows
    ]


async def get_run_detail(
    db: AsyncSession, organization_id: uuid.UUID, run_id: uuid.UUID
) -> RunDetailOut | None:
    query = (
        select(Run, Agent.name)
        .join(Agent, Agent.id == Run.agent_id)
        .where(Agent.organization_id == organization_id, Run.id == run_id)
        .options(selectinload(Run.spans).selectinload(Span.tool_calls))
    )
    row = (await db.execute(query)).first()
    if row is None:
        return None

    run, agent_name = row
    return RunDetailOut(
        id=run.id,
        agent_name=agent_name,
        status=run.status,
        started_at=run.started_at,
        ended_at=run.ended_at,
        risk_score=run.risk_score,
        spans=[SpanOut.model_validate(span) for span in run.spans],
    )
