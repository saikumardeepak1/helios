from fastapi import FastAPI

from app.api.routes.alerts import router as alerts_router
from app.api.routes.auth import router as auth_router
from app.api.routes.cost import router as cost_router
from app.api.routes.health import router as health_router
from app.api.routes.ingest import router as ingest_router
from app.api.routes.runs import router as runs_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import CorrelationIdMiddleware

settings = get_settings()
configure_logging()

app = FastAPI(
    title="Helios API",
    description="AI Agent Observability Platform — ingestion, dashboard, and auth API.",
    version="0.1.0",
)

app.add_middleware(CorrelationIdMiddleware)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(ingest_router)
app.include_router(runs_router)
app.include_router(cost_router)
app.include_router(alerts_router)
