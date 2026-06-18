from __future__ import annotations

import json
from typing import Any

from app.models.script import Script
from app.models.task import Task, TaskType
from app.models.user import User
from app.services.script.task_titles import friendly_task_title
from app.services.task_worker import storyboard_generate_task
from sqlalchemy.orm import Session


def default_storyboard_generation_params(script_id: int) -> dict[str, Any]:
    return {
        "script_id": script_id,
        "model": None,
        "temperature": 0.7,
        "frames_per_scene": 7,
        "max_frames": None,
        "scene_numbers": None,
        "use_plan": True,
    }


def queue_storyboard_generation_task(
    db: Session,
    user: User,
    script: Script,
    *,
    params: dict[str, Any] | None = None,
    title: str | None = None,
    description: str = "异步分镜结构生成",
    prompt: str | None = None,
    target_business_id: str | None = None,
) -> Task:
    payload = default_storyboard_generation_params(script.id)
    if params:
        payload.update(params)
    payload["script_id"] = script.id

    episode = script.episode if script.episode else None
    story = episode.story if episode else None
    task = Task(
        title=title or friendly_task_title("生成分镜", script, episode, story),
        description=description,
        task_type=TaskType.STORYBOARD_GENERATION,
        prompt=prompt or f"Storyboard generation for script {script.id}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=user.id,
        target_business_id=target_business_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    storyboard_generate_task.delay(task.id, payload, user.id)
    return task
