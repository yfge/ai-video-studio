from __future__ import annotations

import json

from app.models.script import Script
from app.models.task import Task
from app.models.user import User
from app.repositories.script_repository import ScriptRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.production_canvas import (
    ProductionCanvasSkillExecuteRequest,
    ProductionCanvasSkillExecuteResponse,
    ProductionCanvasSkillResult,
)
from app.services.production_canvas.skills import list_canvas_skill_definitions
from sqlalchemy.orm import Session


def skill_definition(skill_id: str):
    return next(
        (skill for skill in list_canvas_skill_definitions() if skill.id == skill_id),
        None,
    )


def blocked_result(
    request: ProductionCanvasSkillExecuteRequest,
    *,
    title: str,
    detail: str,
    required_inputs: list[str] | None = None,
) -> ProductionCanvasSkillExecuteResponse:
    skill = skill_definition(request.skill)
    outputs: dict[str, object] = {}
    if required_inputs:
        outputs["required_inputs"] = required_inputs
    if request.run_id:
        outputs["canvas_run_id"] = request.run_id
    return ProductionCanvasSkillExecuteResponse(
        skill_result=ProductionCanvasSkillResult(
            skill=request.skill,
            label=skill.label if skill else request.skill,
            status="blocked",
            title=title,
            detail=detail,
            outputs=outputs,
            reuse_targets=skill.reuse_targets if skill else [],
        )
    )


def load_script(db: Session, user: User, script_id: int | None) -> Script | None:
    if script_id is None:
        return None
    user_id = None if user.is_admin or user.is_superuser else user.id
    return ScriptRepository(db).get_with_relations(
        script_id=script_id,
        user_id=user_id,
    )


def load_task(db: Session, user: User, task_id: int | None) -> Task | None:
    if task_id is None:
        return None
    task = TaskRepository(db).get_by_id(task_id)
    if task is None or getattr(task, "is_deleted", False):
        return None
    if not (user.is_admin or user.is_superuser) and task.user_id != user.id:
        return None
    return task


def decode_parameters(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return {"_raw_parameters": raw}
    return value if isinstance(value, dict) else {"_raw_parameters": value}
