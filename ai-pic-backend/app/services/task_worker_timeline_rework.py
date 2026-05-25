from __future__ import annotations

from typing import Any, Dict

from app.core.celery_app import celery_app


@celery_app.task(name="tasks.timeline_clip_rework_video_generate")
def timeline_clip_rework_video_generate_task(
    task_id: int,
    payload: Dict[str, Any],
    user_id: int,
) -> None:
    from app.core.database import get_task_db
    from app.services.ai_service import ai_service
    from app.services.task_agent_run_persistence import persist_task_agent_run
    from app.services.timeline_clip_video_rework_submission import (
        TimelineClipVideoReworkSubmissionService,
    )

    with get_task_db() as db:
        if not ai_service.ai_manager:
            raise RuntimeError("AI管理器未初始化，无法提交视频重做任务")
        service = TimelineClipVideoReworkSubmissionService(db, ai_service.ai_manager)
        service.submit(task_id=task_id, payload=payload, user_id=user_id)
    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="video_generation",
    )
