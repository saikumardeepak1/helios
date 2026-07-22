from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Helios API",
    description="AI Agent Observability Platform — ingestion, dashboard, and auth API.",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(auth_router)
