import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.models import Run, Span
from app.services.cost_service import calculate_run_cost
from app.services.pii_service import scan_spans

logger = logging.getLogger(__name__)


async def _analyze_run_async(run_id: str) -> None:
    """Post-ingestion analysis pipeline: cost rollup and PII detection, then
    (in later issues) prompt-injection detection and risk scoring, which
    will combine these detectors' findings into Alert rows.

    Uses its own NullPool engine rather than the API's shared engine: each
    RQ job runs inside its own asyncio.run() call (a fresh event loop every
    time), and a pooled connection checked out under one loop cannot be
    reused once that loop closes. NullPool opens and closes a fresh
    connection per checkout, so there's nothing to leak across loops.
    """
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
            pii_findings = scan_spans(list(spans))
            if pii_findings:
                total = sum(len(f) for f in pii_findings.values())
                logger.warning(
                    "PII detected in run %s: %d finding(s) across %d span(s)",
                    run_id,
                    total,
                    len(pii_findings),
                )
    finally:
        await engine.dispose()


def analyze_run(run_id: str) -> None:
    asyncio.run(_analyze_run_async(run_id))
