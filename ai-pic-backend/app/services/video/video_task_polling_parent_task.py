from __future__ import annotations

from typing import Optional

from app.models.task import Task, TaskStatus
from app.models.video_generation_task import VideoGenerationTaskStatus
from app.services.task_agent_run_persistence import persist_task_agent_run


def refresh_parent_task_status(db, video_task_repo, task_id: Optional[int]) -> None:
    """Refresh parent Task.status based on child VideoGenerationTask statuses."""
    if not task_id:
        return

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return

    tasks = video_task_repo.list_by_task_id(task_id)
    if not tasks:
        return

    terminal = {
        VideoGenerationTaskStatus.SUCCEEDED,
        VideoGenerationTaskStatus.FAILED,
        VideoGenerationTaskStatus.TIMEOUT,
    }
    if any(t.status not in terminal for t in tasks):
        task.status = TaskStatus.PROCESSING
        db.commit()
        return

    if any(
        t.status in {VideoGenerationTaskStatus.FAILED, VideoGenerationTaskStatus.TIMEOUT}
        for t in tasks
    ):
        task.status = TaskStatus.FAILED
        if not task.error_message:
            for sub in tasks:
                sub_err = getattr(sub, "error_message", None)
                if isinstance(sub_err, str) and sub_err.strip():
                    task.error_message = sub_err.strip()
                    break
    else:
        task.status = TaskStatus.COMPLETED
    db.commit()

    if task.status in {
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    }:
        persist_task_agent_run(
            task_id=task.id,
            user_id=task.user_id,
            kind="video_generation",
            db_session=db,
        )

