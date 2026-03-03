"""Celery tasks for background operations."""

import structlog
from datetime import datetime, timezone, timedelta

from infrastructure.celery_app import celery_app
from infrastructure.storage import StorageService
from api.config import settings

logger = structlog.get_logger()


@celery_app.task(name="infrastructure.tasks.purge_expired_images", queue="async")
def purge_expired_images() -> dict[str, int]:
    """Remove images older than the configured TTL from MinIO.

    Runs periodically via Celery Beat (every 5 minutes).
    Ensures biometric data is not retained beyond 15 minutes (GDPR compliance).
    """
    storage = StorageService()
    ttl = timedelta(minutes=settings.minio_image_ttl_minutes)
    cutoff = datetime.now(timezone.utc) - ttl
    total_deleted = 0

    for bucket in StorageService.BUCKETS:
        try:
            from minio import Minio

            client = storage._client
            objects = client.list_objects(bucket)
            for obj in objects:
                if obj.last_modified and obj.last_modified < cutoff:
                    client.remove_object(bucket, obj.object_name)
                    total_deleted += 1
        except Exception as e:
            logger.error("purge_expired_images.error", bucket=bucket, error=str(e))

    logger.info("purge_expired_images.complete", deleted=total_deleted)
    return {"deleted": total_deleted}
