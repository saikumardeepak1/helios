import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_session
from app.core.db import get_db
from app.models import User
from app.schemas.dashboard import AlertOut
from app.services.dashboard_service import get_alert, list_alerts

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut], summary="List security alerts")
async def list_alerts_route(
    severity: str | None = Query(
        default=None, description="Filter to alerts with this exact severity."
    ),
    category: str | None = Query(
        default=None, description="Filter to alerts with this exact category."
    ),
    limit: int = Query(default=50, le=200, gt=0, description="Max alerts to return."),
    offset: int = Query(default=0, ge=0, description="Number of alerts to skip, for pagination."),
    current_user: User = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> list[AlertOut]:
    """Alerts for the caller's organization, most recent first. Raised by
    the risk scoring engine when a run's PII/prompt-injection findings
    push its risk score past the alert threshold (see docs/TDD.md).
    """
    return await list_alerts(
        db,
        current_user.organization_id,
        severity=severity,
        category=category,
        limit=limit,
        offset=offset,
    )


@router.get("/{alert_id}", response_model=AlertOut, summary="Get one alert")
async def get_alert_route(
    alert_id: uuid.UUID,
    current_user: User = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> AlertOut:
    """Full detail for a single alert. Use `run_id` on the response to
    fetch the triggering run's full span timeline via `GET /v1/runs/{id}`.
    404s for an alert outside the caller's organization, same as one that
    doesn't exist.
    """
    alert = await get_alert(db, current_user.organization_id, alert_id)
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    return alert
