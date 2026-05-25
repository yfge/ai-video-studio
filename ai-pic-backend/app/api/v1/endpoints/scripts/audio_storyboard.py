"""Audio timeline to storyboard placeholder endpoints and task processor."""

from __future__ import annotations

import json

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.audio.storyboard_from_timeline import (
    generate_storyboard_from_episode_audio_timeline,
)
from app.services.script.task_titles import friendly_task_title
from app.services.task_worker import script_audio_storyboard_generate_task
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .audio_pipeline_utils import (
    load_script_with_access,
    mark_pipeline_endpoint_deprecated,
    run_async_task_sync,
    update_task_progress,
)

router = APIRouter()


class ScriptAudioStoryboardGenerateRequest(BaseModel):
    overwrite_existing: bool = Field(
        False,
        description="Overwrite existing storyboard placeholders",
    )
    min_pause_seconds: float = Field(
        1.5,
        ge=0.0,
        le=10.0,
        description="Pause beat threshold in seconds for placeholder generation",
    )


@router.post(
    "/{script_id}/storyboard/from-audio-timeline/generate-async",
    deprecated=True,
)
async def generate_storyboard_from_audio_timeline_async(
    script_id: int,
    body: ScriptAudioStoryboardGenerateRequest,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Queue async storyboard placeholder generation from episode audio timeline."""
    script = load_script_with_access(db, script_id, current_user)
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")

    story = script.episode.story if script.episode else None
    episode = script.episode if script.episode else None
    params = body.model_dump()
    params["script_id"] = script_id

    task = Task(
        title=friendly_task_title("分镜占位生成", script, episode, story),
        description="根据对白时间轴生成分镜帧占位（audio_timeline）",
        task_type=TaskType.STORYBOARD_GENERATION,
        prompt=(
            "Storyboard placeholder generation from audio timeline "
            f"for script {script_id}"
        ),
        parameters=json.dumps(params, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    mark_pipeline_endpoint_deprecated(
        response,
        successor_path=f"/api/v1/scripts/{script_id}/timeline-pipeline/generate-async",
    )
    script_audio_storyboard_generate_task.delay(task.id, params, current_user.id)
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


def _process_script_audio_storyboard_task(
    task_id: int,
    payload: dict,
    user_id: int,
) -> None:
    """Celery worker handler for storyboard placeholders from audio timeline."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        task_repo = TaskRepository(db)
        user_repo = UserRepository(db)
        task = task_repo.get_by_id(task_id)
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script_id = int(payload.get("script_id"))
        overwrite_existing = bool(payload.get("overwrite_existing"))
        min_pause_seconds = float(payload.get("min_pause_seconds") or 1.5)
        min_pause_ms = max(0, int(round(min_pause_seconds * 1000)))

        async def _run() -> None:
            user = user_repo.get_by_id(user_id)
            if not user:
                raise RuntimeError("user_not_found")

            script = load_script_with_access(db, script_id, user)
            if not script:
                raise RuntimeError("script_not_found")

            episode = script.episode
            if not episode:
                raise RuntimeError("episode_not_found")

            update_task_progress(db, task, "根据时间轴生成分镜帧占位中…")
            generate_storyboard_from_episode_audio_timeline(
                db,
                script=script,
                episode=episode,
                overwrite_existing=overwrite_existing,
                min_pause_duration_ms=min_pause_ms,
                legacy_support_view=True,
            )

        run_async_task_sync(_run)

        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"script:{script_id}:storyboard_from_audio_timeline"
            update_task_progress(db, task, "分镜帧占位生成完成")
    except Exception as exc:
        task = TaskRepository(db).get_by_id(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            update_task_progress(db, task, f"分镜帧占位生成失败：{exc}")
    finally:
        db.close()


__all__ = [
    "router",
    "ScriptAudioStoryboardGenerateRequest",
    "generate_storyboard_from_audio_timeline_async",
    "_process_script_audio_storyboard_task",
]
