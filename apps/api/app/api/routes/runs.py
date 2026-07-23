import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_session
from app.core.db import get_db
from app.models import User
from app.schemas.dashboard import RunDetailOut, RunSummaryOut
from app.services.dashboard_service import get_run_detail, list_runs

router = APIRouter(prefix="/v1/runs", tags=["runs"])


@router.get("", response_model=list[RunSummaryOut], summary="List agent runs")
async def list_runs_route(
    run_status: str | None = Query(
        default=None, alias="status", description="Filter to runs with this exact status."
    ),
    agent_id: uuid.UUID | None = Query(
        default=None, description="Filter to runs from this agent only."
    ),
    limit: int = Query(default=50, le=200, gt=0, description="Max runs to return."),
    offset: int = Query(default=0, ge=0, description="Number of runs to skip, for pagination."),
    current_user: User = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> list[RunSummaryOut]:
    """Runs for the caller's organization, most recent first. Powers the
    trace explorer's run list.
    """
    return await list_runs(
        db,
        current_user.organization_id,
        status=run_status,
        agent_id=agent_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{run_id}", response_model=RunDetailOut, summary="Get one run's full trace")
async def get_run_route(
    run_id: uuid.UUID,
    current_user: User = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> RunDetailOut:
    """Full detail for a single run, including every span (with its tool
    calls) recorded during it — flat, not nested; reconstruct the
    parent/child tree client-side from each span's `parent_span_id`.
    404s for a run outside the caller's organization, same as one that
    doesn't exist.
    """
    run = await get_run_detail(db, current_user.organization_id, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Run not found")
    return run
