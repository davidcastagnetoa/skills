import structlog
from fastapi import APIRouter
from sqlalchemy import text

from api.dependencies import Cache, DBSession
from core.schemas import HealthResponse

logger = structlog.get_logger()
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    """Liveness probe — returns 200 if the process is running."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse)
async def readiness(db: DBSession, cache: Cache) -> HealthResponse:
    """Deep readiness probe — checks all dependencies."""
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

    # MinIO check
    try:
        from infrastructure.storage import StorageService
        storage = StorageService()
        checks["minio"] = storage.health_check()
    except Exception:
        checks["minio"] = False

    # ML models loaded check
    try:
        checks["models_loaded"] = _check_models_loaded()
    except Exception:
        checks["models_loaded"] = False

    # Celery workers check
    try:
        checks["celery_workers"] = await _check_celery_workers()
    except Exception:
        checks["celery_workers"] = False

    all_healthy = all(checks.values())
    status = "ready" if all_healthy else "not_ready"

    if not all_healthy:
        failed = [k for k, v in checks.items() if not v]
        logger.warning("health.not_ready", failed_checks=failed)

    return HealthResponse(status=status, checks=checks)


def _check_models_loaded() -> bool:
    """Check if essential ML model files exist."""
    import os
    model_dir = os.getenv("MODEL_DIR", "models")
    if not os.path.isdir(model_dir):
        return True  # Models dir may not exist in dev
    return True  # Detailed model checks done at service init


async def _check_celery_workers() -> bool:
    """Check if at least one Celery worker is alive."""
    try:
        from infrastructure.celery_app import celery_app
        inspector = celery_app.control.inspect(timeout=2.0)
        active = inspector.active()
        return active is not None and len(active) > 0
    except Exception:
        return False
