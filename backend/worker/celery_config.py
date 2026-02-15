import os
from celery import Celery

# Define Redis URL (default to localhost)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery
celery_app = Celery(
    "golf_coach_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Configuration for stability
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # This ensures that if the worker crashes, the task is re-queued
    task_acks_late=True,
)