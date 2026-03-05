"""Watchdog for monitoring and auto-recovering Celery workers and connections.

Runs as a Celery Beat scheduled task to check worker health
and trigger restarts if workers are unresponsive.
"""

import structlog

logger = structlog.get_logger()


async def check_worker_health(celery_app) -> dict[str, bool]:
    """Check if Celery workers are alive and responsive.

    Returns:
        Dict of worker_name → is_healthy.
    """
    try:
        inspector = celery_app.control.inspect(timeout=3.0)
        ping_result = inspector.ping()
        if ping_result is None:
            logger.warning("watchdog.no_workers_responding")
            return {}

        health = {}
        for worker_name, response in ping_result.items():
            health[worker_name] = response.get("ok") == "pong"

        return health
    except Exception:
        logger.exception("watchdog.health_check_failed")
        return {}


def restart_unresponsive_workers(celery_app, unhealthy_workers: list[str]) -> None:
    """Send pool restart signal to unresponsive workers.

    This uses Celery's remote control to restart the worker pool,
    which is less disruptive than killing the process.
    """
    for worker in unhealthy_workers:
        try:
            celery_app.control.pool_restart(
                destination=[worker],
                reload=True,
            )
            logger.info("watchdog.worker_restart_sent", worker=worker)
        except Exception:
            logger.exception("watchdog.restart_failed", worker=worker)


async def ensure_db_connection(db_session) -> bool:
    """Verify and reconnect database if needed."""
    try:
        from sqlalchemy import text
        await db_session.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.warning("watchdog.db_reconnecting")
        try:
            await db_session.rollback()
            await db_session.execute(text("SELECT 1"))
            logger.info("watchdog.db_reconnected")
            return True
        except Exception:
            logger.error("watchdog.db_reconnect_failed")
            return False


async def ensure_redis_connection(redis_client) -> bool:
    """Verify and reconnect Redis if needed."""
    try:
        await redis_client.ping()
        return True
    except Exception:
        logger.warning("watchdog.redis_reconnecting")
        try:
            await redis_client.ping()
            return True
        except Exception:
            logger.error("watchdog.redis_reconnect_failed")
            return False
