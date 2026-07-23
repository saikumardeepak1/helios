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

OPENAPI_TAGS = [
    {"name": "health", "description": "Unauthenticated liveness check."},
    {
        "name": "auth",
        "description": "Dashboard login/session management and API key issuance.",
    },
    {
        "name": "ingest",
        "description": "Trace ingestion — called by helios-sdk, authenticated with an API key "
        "rather than a session.",
    },
    {"name": "runs", "description": "Trace explorer: browse and inspect agent runs."},
    {"name": "cost", "description": "Cost analytics rolled up from ingested runs."},
    {
        "name": "alerts",
        "description": "Security alerts raised by the risk scoring engine.",
    },
]

app = FastAPI(
    title="Helios API",
    description=(
        "AI Agent Observability Platform — ingestion, dashboard, and auth API.\n\n"
        "Two auth schemes are used depending on the route: an **API key** "
        "(`Authorization: Bearer hel_live_...`) on `/v1/ingest/*`, and a "
        "**JWT session** (`Authorization: Bearer <access_token>` from "
        "`/v1/auth/login`) on every other authenticated route."
    ),
    version="0.1.0",
    openapi_tags=OPENAPI_TAGS,
)

app.add_middleware(CorrelationIdMiddleware)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(ingest_router)
app.include_router(runs_router)
app.include_router(cost_router)
app.include_router(alerts_router)
