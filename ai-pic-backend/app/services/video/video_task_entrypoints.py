from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.database import SessionLocal
from app.services.ai_service import ai_service
from app.services.video.video_task_polling_service import VideoTaskPollingService
from app.services.video.video_task_submission_service import VideoTaskSubmissionService


def submit_storyboard_video_tasks(
    task_id: int,
    script_id: int,
    frame_indexes: Optional[List[int]],
    selections: Optional[List[Dict[str, Any]]],
    options: Optional[Dict[str, Any]],
) -> None:
    db = SessionLocal()
    try:
        if not ai_service.ai_manager:
            raise RuntimeError("AI管理器未初始化，无法提交视频任务")
        service = VideoTaskSubmissionService(db, ai_service.ai_manager)
        service.submit_storyboard_video_tasks(
            task_id=task_id,
            script_id=script_id,
            frame_indexes=frame_indexes,
            selections=selections,
            options=options,
        )
    finally:
        db.close()


def poll_pending_video_tasks(limit: int = 50) -> int:
    db = SessionLocal()
    try:
        if not ai_service.ai_manager:
            return 0
        service = VideoTaskPollingService(db, ai_service.ai_manager)
        return service.poll_pending_tasks(limit=limit)
    finally:
        db.close()
