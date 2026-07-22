import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_session
from app.core.db import get_db
from app.models import User
from app.schemas.dashboard import AlertOut
from app.services.dashboard_service import get_alert, list_alerts

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
async def list_alerts_route(
    severity: str | None = None,
    category: str | None = None,
    limit: int = Query(default=50, le=200, gt=0),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> list[AlertOut]:
    return await list_alerts(
        db,
        current_user.organization_id,
        severity=severity,
        category=category,
        limit=limit,
        offset=offset,
    )


@router.get("/{alert_id}", response_model=AlertOut)
async def get_alert_route(
    alert_id: uuid.UUID,
    current_user: User = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> AlertOut:
    alert = await get_alert(db, current_user.organization_id, alert_id)
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    return alert
