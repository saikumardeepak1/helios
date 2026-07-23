from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_api_key
from app.core.db import get_db
from app.models import Organization
from app.schemas.ingestion import IngestTraceRequest, IngestTraceResponse
from app.services.ingestion_service import ingest_run
from app.workers.queue import get_queue
from app.workers.tasks import analyze_run

router = APIRouter(prefix="/v1/ingest", tags=["ingest"])


@router.post(
    "/traces",
    response_model=IngestTraceResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest an agent run",
)
async def ingest_trace(
    payload: IngestTraceRequest,
    organization: Organization = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
) -> IngestTraceResponse:
    """Store one agent run's spans and tool calls, then queue it for
    background analysis (cost calculation, PII/prompt-injection detection,
    and risk scoring).

    Authenticated with an API key (`Authorization: Bearer hel_live_...`),
    not a user session — this is the endpoint `helios-sdk` calls, not one a
    dashboard user calls directly. The agent named in the payload is
    created automatically on first use and its `version` is kept in sync
    on every subsequent call.

    Returns 202 immediately; analysis (and therefore cost/risk data)
    completes asynchronously, typically within a couple of seconds.
    """
    run, span_count = await ingest_run(db, organization, payload)

    get_queue().enqueue(analyze_run, str(run.id))

    return IngestTraceResponse(run_id=run.id, status=run.status, span_count=span_count)
