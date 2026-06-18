from __future__ import annotations

import json
from typing import Any, Dict

from app.models.task import Task, TaskType
from app.models.user import User
from app.schemas.generation_requests import ScriptGenerationRequest
from app.services.task_worker import script_generate_task
from sqlalchemy.orm import Session


def build_script_generation_task_params(
    request: ScriptGenerationRequest,
) -> Dict[str, Any]:
    params = request.model_dump()
    fields_set = getattr(request, "model_fields_set", None)
    if fields_set is None:
        fields_set = getattr(request, "__fields_set__", set())
    if "generation_mode" not in fields_set:
        params["generation_mode"] = "production"
    else:
        params["generation_mode"] = params.get("generation_mode") or "production"
    if params["generation_mode"] == "standard":
        params["auto_timeline_pipeline"] = bool(params.get("auto_timeline_pipeline"))
    elif params.get("auto_timeline_pipeline") is None:
        params["auto_timeline_pipeline"] = True
    return params


def queue_script_generation_task(
    db: Session,
    user: User,
    request: ScriptGenerationRequest,
    *,
    title: str | None = None,
    description: str = "异步剧本生成",
    prompt: str | None = None,
    target_business_id: str | None = None,
) -> Task:
    params = build_script_generation_task_params(request)
    task = Task(
        title=title or f"生成剧本 - 剧集{request.episode_id}",
        description=description,
        task_type=TaskType.SCRIPT_GENERATION,
        prompt=prompt or f"Script for episode {request.episode_id}",
        parameters=json.dumps(params, ensure_ascii=False),
        user_id=user.id,
        target_business_id=target_business_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    script_generate_task.delay(task.id, params, user.id)
    return task
