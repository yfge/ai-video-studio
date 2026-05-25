"""Script generation task queue endpoints."""

from __future__ import annotations

import json
from typing import Any, Dict

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.schemas.generation_requests import ScriptGenerationRequest
from app.services.task_worker import script_generate_task
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/generate-async")
async def generate_script_async(
    request: ScriptGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    params = build_script_generation_task_params(request)
    task = Task(
        title=f"生成剧本 - 剧集{request.episode_id}",
        description="异步剧本生成",
        task_type=TaskType.SCRIPT_GENERATION,
        prompt=f"Script for episode {request.episode_id}",
        parameters=json.dumps(params, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    script_generate_task.delay(task.id, params, current_user.id)
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


def build_script_generation_task_params(
    request: ScriptGenerationRequest,
) -> Dict[str, Any]:
    params = request.dict()
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
