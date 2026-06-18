from __future__ import annotations

import json

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.script.task_titles import friendly_task_title
from app.services.script.timeline_storyboard_queue import (
    generate_storyboard_placeholders_and_queue_images,
)
from app.services.storyboard.storyboard_image_autogen import (
    storyboard_image_queue_progress_message,
)
from app.services.task_worker import timeline_pipeline_generate_task
from app.services.timeline_pipeline_runner import run_timeline_main_chain
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .audio_pipeline_utils import (
    format_pipeline_error,
    load_script_with_access,
    run_async_task_sync,
    update_task_progress,
)

router = APIRouter()


class TimelinePipelineGenerateRequest(BaseModel):
    tts_model: str | None = Field(None, description="TTS model (default speech-2.6-hd)")
    timing_model: str | None = Field(None, description="Timeline LLM model")
    overwrite_audio: bool = Field(False, description="Overwrite existing scene audio")
    overwrite_timeline: bool = Field(False, description="Overwrite existing timeline")
    overwrite_storyboard: bool = Field(False, description="Overwrite storyboard")
    min_pause_seconds: float = Field(
        1.5,
        description="Minimum pause duration for video clips/storyboard placeholders",
    )
    use_duration_control: bool = Field(
        False,
        description="Enable Duration Orchestrator for tighter duration control",
    )


@router.post("/{script_id}/timeline-pipeline/generate-async")
async def generate_timeline_pipeline_async(
    script_id: int,
    body: TimelinePipelineGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Queue one-click timeline pipeline (dialogue audio -> timeline -> storyboard)."""
    script = load_script_with_access(db, script_id, current_user)
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")

    story = script.episode.story if script.episode else None
    episode = script.episode if script.episode else None
    params = body.model_dump()
    params["script_id"] = script_id

    task = Task(
        title=friendly_task_title("一键时间轴流水线", script, episode, story),
        description="一键生成对白音轨、时间轴、分镜帧占位",
        task_type=TaskType.TIMELINE_PIPELINE,
        prompt=f"Timeline pipeline for script {script_id}",
        parameters=json.dumps(params, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    timeline_pipeline_generate_task.delay(task.id, params, current_user.id)
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


def _process_timeline_pipeline_task(task_id: int, payload: dict, user_id: int) -> None:
    """Celery worker handler for the timeline pipeline."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        task_repo = TaskRepository(db)
        task = task_repo.get_by_id(task_id)
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script_id = int(payload.get("script_id"))
        overwrite_audio = bool(payload.get("overwrite_audio"))
        overwrite_timeline = bool(payload.get("overwrite_timeline"))
        overwrite_storyboard = bool(payload.get("overwrite_storyboard"))
        tts_model = payload.get("tts_model") or "speech-2.6-hd"
        timing_model = payload.get("timing_model")
        min_pause_seconds = float(payload.get("min_pause_seconds") or 1.5)
        min_pause_ms = max(0, int(round(min_pause_seconds * 1000)))
        use_duration_control = bool(payload.get("use_duration_control", False))

        async def _run() -> None:
            user = UserRepository(db).get_by_id(user_id)
            if not user:
                raise RuntimeError("user_not_found")

            script = load_script_with_access(db, script_id, user)
            if not script:
                raise RuntimeError("script_not_found")

            episode = script.episode
            if not episode:
                raise RuntimeError("episode_not_found")

            story = episode.story
            if not story:
                raise RuntimeError("story_not_found")

            def _progress_cb(message: str) -> None:
                update_task_progress(db, task, f"步骤 1-3/5：{message}")

            main_chain = await run_timeline_main_chain(
                db,
                story=story,
                episode=episode,
                script=script,
                tts_model=str(tts_model),
                timing_model=timing_model,
                overwrite_audio=overwrite_audio,
                overwrite_timeline=overwrite_timeline,
                min_pause_duration_ms=min_pause_ms,
                use_duration_control=use_duration_control,
                user_id=user.id,
                progress_callback=_progress_cb,
            )
            timeline = main_chain.timeline

            update_task_progress(db, task, "步骤 4/5：生成分镜帧占位…")
            image_result = generate_storyboard_placeholders_and_queue_images(
                db,
                parent_task=task,
                script=script,
                episode=episode,
                timeline=timeline,
                user_id=user.id,
                overwrite_storyboard=overwrite_storyboard,
                min_pause_ms=min_pause_ms,
            )
            update_task_progress(
                db,
                task,
                storyboard_image_queue_progress_message(
                    image_result,
                    prefix="步骤 5/5",
                ),
            )

        run_async_task_sync(_run)

        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"script:{script_id}:timeline_pipeline"
            update_task_progress(db, task, "一键时间轴流水线完成")
    except Exception as exc:
        task = TaskRepository(db).get_by_id(task_id)
        if task:
            error_message = format_pipeline_error(exc)
            task.status = TaskStatus.FAILED
            task.error_message = error_message
            if isinstance(exc, HTTPException):
                _persist_pipeline_error_detail(task, exc.detail)
            update_task_progress(db, task, f"流水线失败：{error_message}")
    finally:
        db.close()


def _persist_pipeline_error_detail(task: Task, detail: object) -> None:
    if not isinstance(detail, dict):
        return
    sanitized = _sanitize_pipeline_error_detail(detail)
    if not sanitized:
        return
    try:
        params = json.loads(task.parameters) if task.parameters else {}
    except Exception:
        params = {}
    if not isinstance(params, dict):
        params = {}
    params["pipeline_error"] = sanitized
    task.parameters = json.dumps(params, ensure_ascii=False)


def _sanitize_pipeline_error_detail(detail: dict) -> dict:
    allowed = {
        "message",
        "errors",
        "batch_index",
        "batch_count",
        "clip_ids",
        "provider",
        "model",
        "usage",
        "finish_reason",
        "max_tokens",
        "repair_attempts",
    }
    sanitized = {key: detail[key] for key in allowed if key in detail}
    message = sanitized.get("message")
    if isinstance(message, str) and "timeline shot plan" in message:
        sanitized["stage"] = "timeline_shot_plan"
    elif sanitized:
        sanitized["stage"] = str(detail.get("stage") or "timeline_pipeline")
    if "errors" in sanitized:
        sanitized["errors"] = _sanitize_error_items(sanitized["errors"])
    return sanitized


def _sanitize_error_items(errors: object) -> list[dict]:
    if not isinstance(errors, list):
        return []
    sanitized: list[dict] = []
    for item in errors:
        if not isinstance(item, dict):
            sanitized.append({"msg": str(item)})
            continue
        sanitized.append(
            {
                key: value
                for key, value in item.items()
                if key not in {"input", "ctx", "url"}
            }
        )
    return sanitized
