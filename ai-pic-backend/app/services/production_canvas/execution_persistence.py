from __future__ import annotations

import json

from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasNodeExecution,
    ProductionCanvasSkillExecuteResponse,
    ProductionCanvasSkillResult,
)
from app.services.production_canvas.run_persistence import _canvas_run_task
from sqlalchemy.orm import Session


def save_canvas_skill_result(
    db: Session,
    user: User,
    run_id: str,
    result: ProductionCanvasSkillResult,
) -> bool:
    response = ProductionCanvasSkillExecuteResponse(skill_result=result)
    return save_canvas_execution_response(db, user, run_id, response)


def _response_executions(
    response: ProductionCanvasSkillExecuteResponse,
) -> list[ProductionCanvasNodeExecution]:
    if response.executions:
        return response.executions
    return [
        ProductionCanvasNodeExecution(
            skill_result=response.skill_result,
            task_id=response.task_id,
            task_status=response.task_status,
            node_id=response.node_id,
            resolved_inputs=response.resolved_inputs,
        )
    ]


def save_canvas_execution_response(
    db: Session,
    user: User,
    run_id: str,
    response: ProductionCanvasSkillExecuteResponse,
) -> bool:
    task_and_payload = _canvas_run_task(db, user, run_id, for_update=True)
    if task_and_payload is None:
        return False
    task, payload = task_and_payload
    executions = _response_executions(response)
    results_by_skill = {
        execution.skill_result.skill: execution.skill_result.model_dump()
        for execution in executions
    }
    payload["skill_results"] = [
        item
        for item in payload.get("skill_results") or []
        if not isinstance(item, dict) or item.get("skill") not in results_by_skill
    ] + list(results_by_skill.values())

    state = payload.get("saved_state")
    if isinstance(state, dict):
        execution_by_node = {
            execution.node_id: execution
            for execution in executions
            if execution.node_id
        }
        for node in state.get("nodes") or []:
            execution = execution_by_node.get(node.get("id"))
            if execution is None:
                continue
            node["status"] = execution.skill_result.status
            node["outputs"] = {
                **(node.get("outputs") or {}),
                **execution.skill_result.outputs,
            }

    task.parameters = json.dumps(payload, ensure_ascii=False)
    db.commit()
    return True
