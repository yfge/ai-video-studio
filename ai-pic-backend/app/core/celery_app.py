"""
Celery 应用配置

用于统一处理后台任务（故事/剧集/剧本生成等），由独立 worker 进程运行。
"""

from celery import Celery

from app.core.config import settings


def _get_broker_url() -> str:
    # 默认复用 REDIS_URL，后续如需区分可扩展单独的 CELERY_BROKER_URL
    return getattr(settings, "REDIS_URL", "redis://localhost:6379/0")


celery_app = Celery(
    "ai_video_studio",
    broker=_get_broker_url(),
    backend=_get_broker_url(),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_acks_late=True,
    worker_max_tasks_per_child=100,
)

