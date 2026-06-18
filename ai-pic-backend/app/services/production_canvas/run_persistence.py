from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasPlanRequest,
    ProductionCanvasPlanResponse,
)


def persist_canvas_skill_run(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
    plan: ProductionCanvasPlanResponse,
) -> Task:
    payload = plan.model_dump()
    payload.update(
        {
            "kind": "production_canvas_run",
            "prompt": request.prompt,
            "requested_asset_ids": {
                "virtual_ip_id": request.virtual_ip_id,
                "environment_id": request.environment_id,
                "episode_id": request.episode_id,
                "script_id": request.script_id,
                "task_id": request.task_id,
            },
        }
    )
    task = Task(
        title="生产画布整体创建",
        description="Production canvas skill run",
        task_type=TaskType.TEXT_GENERATION,
        status=TaskStatus.COMPLETED,
        prompt=request.prompt,
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    task.result_file_path = f"production_canvas:{task.business_id}"
    db.commit()
    db.refresh(task)
    return task


def attach_canvas_run(
    plan: ProductionCanvasPlanResponse,
    task: Task,
) -> ProductionCanvasPlanResponse:
    return plan.model_copy(update={"run_id": task.business_id, "task_id": task.id})
