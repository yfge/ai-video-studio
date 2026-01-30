from __future__ import annotations

import json
from typing import Any

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.schemas.script_quality import ScriptLintOptions, ScriptLintResult
from app.services.script import ScriptService, get_script_service
from app.services.script_quality import lint_script_content
from app.services.task_worker_script_quality import script_quality_check_task
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

router = APIRouter()


def _service(db: Session = Depends(get_db)) -> ScriptService:
    return get_script_service(db)


@router.post("/{script_id}/quality-check", response_model=ScriptLintResult)
async def quality_check_script(
    script_id: int,
    options: ScriptLintOptions = Body(default_factory=ScriptLintOptions),
    current_user: User = Depends(get_current_active_user),
    service: ScriptService = Depends(_service),
) -> ScriptLintResult:
    """同步质检剧本（仅做 deterministic lint，不调用大模型）。"""
    script = service.get_script(script_id=script_id, user=current_user)
    return lint_script_content(script.content or "", options=options)


@router.post("/{script_id}/quality-check-async")
async def quality_check_script_async(
    script_id: int,
    options: ScriptLintOptions = Body(default_factory=ScriptLintOptions),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: ScriptService = Depends(_service),
) -> dict[str, Any]:
    """异步质检剧本：创建 Task 并交给 Celery 执行。"""
    script = service.get_script(script_id=script_id, user=current_user)

    payload = {"script_id": script_id, "options": options.model_dump(mode="json")}
    task = Task(
        title=f"剧本质检 - {script.title}",
        description="按工业化约束进行脚本质检",
        task_type=TaskType.SCRIPT_REVIEW,
        prompt=f"Script quality check for script {script_id}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
        target_business_id=getattr(script, "business_id", None),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    script_quality_check_task.delay(task.id, payload, current_user.id)
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}
