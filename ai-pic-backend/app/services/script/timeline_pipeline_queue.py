from __future__ import annotations

import json
from typing import Any

from app.models.script import Script
from app.models.task import Task, TaskType
from app.models.user import User
from app.services.script.task_titles import friendly_task_title
from app.services.task_worker import timeline_pipeline_generate_task
from sqlalchemy.orm import Session


def default_timeline_pipeline_params(script_id: int) -> dict[str, Any]:
    return {
        "script_id": script_id,
        "tts_model": None,
        "timing_model": None,
        "overwrite_audio": False,
        "overwrite_timeline": False,
        "overwrite_storyboard": False,
        "min_pause_seconds": 1.5,
        "use_duration_control": False,
    }


def queue_timeline_pipeline_task(
    db: Session,
    user: User,
    script: Script,
    *,
    params: dict[str, Any] | None = None,
    title: str | None = None,
    description: str = "一键生成对白音轨、时间轴、分镜帧占位",
    prompt: str | None = None,
    target_business_id: str | None = None,
) -> Task:
    payload = default_timeline_pipeline_params(script.id)
    if params:
        payload.update(params)
    payload["script_id"] = script.id

    episode = script.episode if script.episode else None
    story = episode.story if episode else None
    task = Task(
        title=title or friendly_task_title("一键时间轴流水线", script, episode, story),
        description=description,
        task_type=TaskType.TIMELINE_PIPELINE,
        prompt=prompt or f"Timeline pipeline for script {script.id}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=user.id,
        target_business_id=target_business_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    timeline_pipeline_generate_task.delay(task.id, payload, user.id)
    return task
