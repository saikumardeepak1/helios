import asyncio
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.logging import correlation_id_var
from app.models import Run, Span
from app.services.cost_service import calculate_run_cost
from app.services.injection_service import scan_spans as scan_spans_for_injection
from app.services.pii_service import scan_spans as scan_spans_for_pii
from app.services.risk_service import ALERT_THRESHOLD, assess_run

logger = logging.getLogger(__name__)


async def _analyze_run_async(run_id: str) -> None:
    """Post-ingestion analysis pipeline: cost rollup, PII detection,
    prompt-injection detection, and risk scoring — which combines the two
    detectors' findings into a 0-100 run risk score and, above threshold,
    Alert rows the security dashboard surfaces.

    Uses its own NullPool engine rather than the API's shared engine: each
    RQ job runs inside its own asyncio.run() call (a fresh event loop every
    time), and a pooled connection checked out under one loop cannot be
    reused once that loop closes. NullPool opens and closes a fresh
    connection per checkout, so there's nothing to leak across loops.
    """
    job_correlation_id = f"job-{uuid.uuid4().hex[:12]}"
    correlation_token = correlation_id_var.set(job_correlation_id)

    settings = get_settings()
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            run = (
                await session.execute(select(Run).where(Run.id == run_id))
            ).scalar_one_or_none()
            if run is None:
                return

            await calculate_run_cost(session, run.id)

            spans = (
                (
                    await session.execute(
                        select(Span)
                        .where(Span.run_id == run.id)
                        .options(selectinload(Span.tool_calls))
                    )
                )
                .scalars()
                .all()
            )
            spans = list(spans)

            pii_findings = scan_spans_for_pii(spans)
            injection_findings = scan_spans_for_injection(spans)

            score = await assess_run(session, run, pii_findings, injection_findings)
            if score >= ALERT_THRESHOLD:
                logger.warning("Run %s scored %d risk points, alert(s) created", run_id, score)
    finally:
        await engine.dispose()
        correlation_id_var.reset(correlation_token)


def analyze_run(run_id: str) -> None:
    # Covered by test_analyze_run_sync_wrapper_runs_in_its_own_event_loop,
    # which runs this in a subprocess (required — asyncio.run() can't nest
    # inside pytest-asyncio's already-running loop) that this process's
    # coverage instance can't observe.
    asyncio.run(_analyze_run_async(run_id))  # pragma: no cover
