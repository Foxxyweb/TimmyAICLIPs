"""
AI Video Clipper — Celery Application
========================================
Konfigurasi Celery untuk background task processing.
Redis digunakan sebagai message broker.
"""

# pyrefly: ignore [missing-import]
from celery import Celery
from config import settings

# Buat Celery app instance
celery_app = Celery(
    "ai_video_clipper",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["workers.tasks"],
)

# Konfigurasi Celery
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="Asia/Jakarta",
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Retry settings
    task_max_retries=3,
    task_default_retry_delay=60,
    
    # Worker settings
    worker_concurrency=1,        # 1 task sekaligus (media processing berat)
    worker_prefetch_multiplier=1,
    
    # Result expiry (24 hours)
    result_expires=86400,
    
    # Routing
    task_routes={
        "workers.tasks.process_video_task": {"queue": "video_processing"},
    },
    task_default_queue="video_processing",
)

if __name__ == "__main__":
    celery_app.start()
