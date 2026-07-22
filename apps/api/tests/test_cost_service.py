from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, CostRecord, Organization, Run, Span
from app.services.cost_service import calculate_run_cost, compute_cost


def test_compute_cost_for_a_known_model() -> None:
    cost = compute_cost("gpt-4o-mini", prompt_tokens=1000, completion_tokens=1000)
    assert cost == Decimal("0.00015") + Decimal("0.0006")


def test_compute_cost_is_zero_for_zero_tokens() -> None:
    assert compute_cost("gpt-4o-mini", prompt_tokens=0, completion_tokens=0) == Decimal("0")


def test_compute_cost_is_zero_for_an_unknown_model() -> None:
    assert compute_cost("some-future-model-v99", prompt_tokens=1000, completion_tokens=1000) == (
        Decimal("0")
    )


async def _seed_run_with_spans(db_session: AsyncSession, spans: list[dict]) -> Run:
    org = Organization(name="Acme Corp")
    agent = Agent(name="support-bot", version="1.0.0")
    org.agents.append(agent)
    db_session.add(org)
    await db_session.flush()

    run = Run(agent_id=agent.id, status="completed", started_at=datetime.now(UTC))
    db_session.add(run)
    await db_session.flush()

    for span_kwargs in spans:
        db_session.add(
            Span(run_id=run.id, kind="llm_call", started_at=datetime.now(UTC), **span_kwargs)
        )
    await db_session.commit()
    return run


@pytest.mark.asyncio
async def test_calculate_run_cost_creates_one_record_per_model(db_session: AsyncSession) -> None:
    run = await _seed_run_with_spans(
        db_session,
        [
            {"model": "gpt-4o-mini", "prompt_tokens": 1000, "completion_tokens": 1000},
            {"model": "gpt-4o-mini", "prompt_tokens": 1000, "completion_tokens": 0},
            {"model": "claude-sonnet-5", "prompt_tokens": 1000, "completion_tokens": 1000},
        ],
    )

    records = await calculate_run_cost(db_session, run.id)

    assert len(records) == 2
    by_model = {r.model: r.cost_usd for r in records}
    assert by_model["gpt-4o-mini"] == Decimal("0.00015") * 2 + Decimal("0.0006")
    assert by_model["claude-sonnet-5"] == Decimal("0.003") + Decimal("0.015")


@pytest.mark.asyncio
async def test_calculate_run_cost_ignores_spans_without_a_model(db_session: AsyncSession) -> None:
    run = await _seed_run_with_spans(
        db_session, [{"model": None, "prompt_tokens": 1000, "completion_tokens": 1000}]
    )

    records = await calculate_run_cost(db_session, run.id)

    assert records == []


@pytest.mark.asyncio
async def test_calculate_run_cost_is_idempotent(db_session: AsyncSession) -> None:
    run = await _seed_run_with_spans(
        db_session, [{"model": "gpt-4o-mini", "prompt_tokens": 1000, "completion_tokens": 1000}]
    )

    await calculate_run_cost(db_session, run.id)
    await calculate_run_cost(db_session, run.id)

    records = (
        (await db_session.execute(select(CostRecord).where(CostRecord.run_id == run.id)))
        .scalars()
        .all()
    )
    assert len(records) == 1
