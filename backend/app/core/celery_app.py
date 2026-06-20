"""
ATELIX ViralClip AI Pipeline — Celery Configuration
Defines the Celery application instance for async task processing.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "atelix_viralclip",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jakarta",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.max_video_duration_seconds + 600,
    task_soft_time_limit=settings.max_video_duration_seconds + 300,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)
