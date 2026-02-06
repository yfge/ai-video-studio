"""
Celery 应用配置

用于统一处理后台任务（故事/剧集/剧本生成等），由独立 worker 进程运行。
"""

import sys
from datetime import timedelta

from app.core.config import settings
from celery import Celery


def _running_under_pytest() -> bool:
    # Avoid connecting to external Redis in unit/script tests.
    return "pytest" in sys.modules


def _get_broker_url() -> str:
    # 默认复用 REDIS_URL，后续如需区分可扩展单独的 CELERY_BROKER_URL
    if _running_under_pytest():
        return "memory://"
    return getattr(settings, "REDIS_URL", "redis://localhost:6379/0")


def _get_backend_url() -> str:
    # Celery does not support "memory://" as result backend.
    if _running_under_pytest():
        return "cache+memory://"
    return getattr(settings, "REDIS_URL", "redis://localhost:6379/0")


celery_app = Celery(
    "ai_video_studio",
    broker=_get_broker_url(),
    backend=_get_backend_url(),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_acks_late=True,
    worker_max_tasks_per_child=100,
    # Default timeout: 30 min hard limit, 25 min soft limit (raises SoftTimeLimitExceeded)
    task_time_limit=1800,
    task_soft_time_limit=1500,
    beat_schedule={
        "poll-video-generation-tasks": {
            "task": "tasks.video_generation_poll",
            "schedule": timedelta(seconds=30),
            "args": (50,),
        },
    },
)

# In pytest, execute tasks eagerly to keep endpoint tests self-contained.
if _running_under_pytest():
    celery_app.conf.update(
        task_always_eager=True,
        task_store_eager_result=False,
    )

# 确保在 Celery 应用初始化后注册所有任务
# 任务定义位于 app.services.task_worker 等模块中，使用显式 name（如 "tasks.virtual_ip_image_generate"）
# 通过导入该模块完成注册，避免 worker 启动时出现 KeyError。
import app.services.task_worker  # noqa: E402,F401
import app.services.task_worker_script_quality  # noqa: E402,F401
import app.services.task_worker_storyboard_media  # noqa: E402,F401
