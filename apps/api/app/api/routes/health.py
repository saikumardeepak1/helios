from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness check")
async def health_check() -> dict[str, str]:
    """Unauthenticated liveness check — used by the Docker Compose
    healthcheck and load balancers. Returns 200 as soon as the process is
    up; it does not verify the database or Redis are reachable.
    """
    return {"status": "ok"}
