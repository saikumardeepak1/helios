import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Agent, CostRecord, Run, Span
from app.schemas.dashboard import (
    AgentCostOut,
    CostSummaryOut,
    DailyCostOut,
    RunDetailOut,
    RunSummaryOut,
    SpanOut,
)


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


async def get_cost_summary(
    db: AsyncSession, organization_id: uuid.UUID, days: int = 30
) -> CostSummaryOut:
    since = datetime.now(UTC) - timedelta(days=days)

    base_query = (
        select(CostRecord, Run, Agent.name)
        .join(Run, Run.id == CostRecord.run_id)
        .join(Agent, Agent.id == Run.agent_id)
        .where(Agent.organization_id == organization_id, Run.started_at >= since)
    )
    rows = (await db.execute(base_query)).all()

    total_usd = Decimal("0")
    cost_by_agent: dict[str, Decimal] = {}
    cost_by_day: dict[str, Decimal] = {}

    for cost_record, run, agent_name in rows:
        total_usd += cost_record.cost_usd
        cost_by_agent[agent_name] = cost_by_agent.get(agent_name, Decimal("0")) + (
            cost_record.cost_usd
        )
        day_key = run.started_at.date().isoformat()
        cost_by_day[day_key] = cost_by_day.get(day_key, Decimal("0")) + cost_record.cost_usd

    return CostSummaryOut(
        total_usd=total_usd,
        by_agent=[
            AgentCostOut(agent_name=name, cost_usd=cost)
            for name, cost in sorted(cost_by_agent.items())
        ],
        by_day=[
            DailyCostOut(day=datetime.fromisoformat(day).date(), cost_usd=cost)
            for day, cost in sorted(cost_by_day.items())
        ],
    )
