from __future__ import annotations

from typing import Optional

from app.models.task import TaskStatus
from app.models.video_generation_task import VideoGenerationTaskStatus
from app.repositories.task_repository import TaskRepository
from app.services.task_agent_run import persist_task_agent_run
from app.services.video.video_task_utils import load_parameters


def refresh_parent_task_status(db, video_task_repo, task_id: Optional[int]) -> None:
    """Refresh parent Task.status based on child VideoGenerationTask statuses."""
    if not task_id:
        return

    task = TaskRepository(db).get_by_id(task_id)
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
        t.status
        in {VideoGenerationTaskStatus.FAILED, VideoGenerationTaskStatus.TIMEOUT}
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
        result_ref = _storyboard_video_result_ref(task, tasks)
        if result_ref:
            task.result_file_path = result_ref
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


def _storyboard_video_result_ref(task, video_tasks) -> str | None:
    params = load_parameters(task.parameters)
    if params.get("timeline_rework"):
        return None
    timeline_id = params.get("timeline_id")
    timeline_version = params.get("timeline_version")
    if timeline_id and timeline_version and params.get("timeline_rework_by_frame"):
        return f"timeline_videos:{timeline_id}:v{timeline_version}:{len(video_tasks)}"
    try:
        script_id = int(params.get("script_id"))
    except (TypeError, ValueError):
        return None
    if not all(
        item.script_id == script_id and item.frame_index is not None
        for item in video_tasks
    ):
        return None
    return f"storyboard_videos:{script_id}:{len(video_tasks)}"
