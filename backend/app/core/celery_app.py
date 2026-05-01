from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    "worker",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=[
        "app.tasks.scanner",
        "app.tasks.reporter",
        "app.tasks.takedown_tracker",
    ],
)

celery_app.conf.task_default_queue = "celery"
