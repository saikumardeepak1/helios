from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, Organization, Run, Span, ToolCall
from app.schemas.ingestion import IngestTraceRequest


async def _get_or_create_agent(
    db: AsyncSession, organization: Organization, name: str, version: str
) -> Agent:
    result = await db.execute(
        select(Agent).where(Agent.organization_id == organization.id, Agent.name == name)
    )
    agent = result.scalar_one_or_none()

    if agent is None:
        agent = Agent(organization_id=organization.id, name=name, version=version)
        db.add(agent)
        await db.flush()
    elif agent.version != version:
        agent.version = version

    return agent


async def ingest_run(
    db: AsyncSession, organization: Organization, payload: IngestTraceRequest
) -> tuple[Run, int]:
    agent = await _get_or_create_agent(
        db, organization, payload.agent.name, payload.agent.version
    )

    run = Run(
        agent_id=agent.id,
        status=payload.run.status,
        started_at=payload.run.started_at,
        ended_at=payload.run.ended_at,
    )
    db.add(run)
    await db.flush()

    spans_by_local_id: dict[str, Span] = {}
    for span_in in payload.run.spans:
        span = Span(
            run_id=run.id,
            kind=span_in.kind,
            model=span_in.model,
            input=span_in.input,
            output=span_in.output,
            prompt_tokens=span_in.prompt_tokens,
            completion_tokens=span_in.completion_tokens,
            started_at=span_in.started_at,
            ended_at=span_in.ended_at,
        )
        db.add(span)
        spans_by_local_id[span_in.local_id] = span

    await db.flush()

    for span_in in payload.run.spans:
        if span_in.parent_local_id is None:
            continue
        parent = spans_by_local_id.get(span_in.parent_local_id)
        if parent is not None:
            spans_by_local_id[span_in.local_id].parent_span_id = parent.id

    for span_in in payload.run.spans:
        span = spans_by_local_id[span_in.local_id]
        for tool_call_in in span_in.tool_calls:
            db.add(
                ToolCall(
                    span_id=span.id,
                    tool_name=tool_call_in.tool_name,
                    arguments=tool_call_in.arguments,
                    result=tool_call_in.result,
                )
            )

    await db.commit()
    await db.refresh(run)

    return run, len(payload.run.spans)
