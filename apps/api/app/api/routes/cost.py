from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_session
from app.core.db import get_db
from app.models import User
from app.schemas.dashboard import CostSummaryOut
from app.services.dashboard_service import get_cost_summary

router = APIRouter(prefix="/v1/cost", tags=["cost"])


@router.get("/summary", response_model=CostSummaryOut)
async def get_cost_summary_route(
    days: int = Query(default=30, gt=0, le=365),
    current_user: User = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> CostSummaryOut:
    return await get_cost_summary(db, current_user.organization_id, days=days)
