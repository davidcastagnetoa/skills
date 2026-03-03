from fastapi import APIRouter
from sqlalchemy import text

from api.dependencies import Cache, DBSession
from core.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    """Liveness probe — returns 200 if the process is running."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse)
async def readiness(db: DBSession, cache: Cache) -> HealthResponse:
    """Readiness probe — checks database and Redis connectivity."""
    checks: dict[str, bool] = {}

    # PostgreSQL check
    try:
        await db.execute(text("SELECT 1"))
        checks["postgresql"] = True
    except Exception:
        checks["postgresql"] = False

    # Redis check
    try:
        checks["redis"] = await cache.health_check()
    except Exception:
        checks["redis"] = False

    all_healthy = all(checks.values())
    return HealthResponse(
        status="ready" if all_healthy else "not_ready",
        checks=checks,
    )
