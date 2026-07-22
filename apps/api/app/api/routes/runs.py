import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_session
from app.core.db import get_db
from app.models import User
from app.schemas.dashboard import RunDetailOut, RunSummaryOut
from app.services.dashboard_service import get_run_detail, list_runs

router = APIRouter(prefix="/v1/runs", tags=["runs"])


@router.get("", response_model=list[RunSummaryOut])
async def list_runs_route(
    run_status: str | None = Query(default=None, alias="status"),
    agent_id: uuid.UUID | None = None,
    limit: int = Query(default=50, le=200, gt=0),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> list[RunSummaryOut]:
    return await list_runs(
        db,
        current_user.organization_id,
        status=run_status,
        agent_id=agent_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{run_id}", response_model=RunDetailOut)
async def get_run_route(
    run_id: uuid.UUID,
    current_user: User = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> RunDetailOut:
    run = await get_run_detail(db, current_user.organization_id, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Run not found")
    return run
