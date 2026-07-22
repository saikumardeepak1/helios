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


@router.post("/traces", response_model=IngestTraceResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_trace(
    payload: IngestTraceRequest,
    organization: Organization = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
) -> IngestTraceResponse:
    run, span_count = await ingest_run(db, organization, payload)

    get_queue().enqueue(analyze_run, str(run.id))

    return IngestTraceResponse(run_id=run.id, status=run.status, span_count=span_count)
