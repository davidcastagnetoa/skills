from celery import Celery

from api.config import settings

celery_app = Celery(
    "verifid",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Task execution
    task_track_started=True,
    task_time_limit=30,
    task_soft_time_limit=25,
    # Worker
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    # Queues
    task_default_queue="cpu",
    task_queues={
        "realtime": {"exchange": "realtime", "routing_key": "realtime"},
        "gpu": {"exchange": "gpu", "routing_key": "gpu"},
        "cpu": {"exchange": "cpu", "routing_key": "cpu"},
        "async": {"exchange": "async", "routing_key": "async"},
    },
    # Results
    result_expires=300,
    # Beat schedule (periodic tasks)
    beat_schedule={
        "purge-expired-images": {
            "task": "infrastructure.tasks.purge_expired_images",
            "schedule": 300.0,  # every 5 minutes
        },
    },
)
