from __future__ import annotations

import json
from datetime import UTC, datetime

from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasNodeExecution,
    ProductionCanvasSavedState,
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
            input_fingerprint=response.input_fingerprint,
        )
    ]


def _definition_snapshot(
    state: ProductionCanvasSavedState | None,
    node_id: str,
) -> tuple[dict, list[dict]]:
    if state is None:
        return {}, []
    node = next((item for item in state.nodes if item.id == node_id), None)
    incoming = [
        edge.model_dump(by_alias=True, mode="json")
        for edge in state.edges
        if edge.to_node == node_id
    ]
    return (
        node.model_dump(by_alias=True, mode="json") if node else {},
        incoming,
    )


def _append_execution_attempts(
    payload: dict,
    executions: list[ProductionCanvasNodeExecution],
    state: ProductionCanvasSavedState | None,
    definition_mode: str,
) -> None:
    attempts = list(payload.get("execution_attempts") or [])
    for execution in executions:
        if not execution.node_id:
            continue
        node, incoming_edges = _definition_snapshot(state, execution.node_id)
        attempts.append(
            {
                "attempt_id": len(attempts) + 1,
                "node_id": execution.node_id,
                "skill": execution.skill_result.skill,
                "status": execution.skill_result.status,
                "definition_version": int(node.get("definition_version") or 1),
                "definition_mode": definition_mode,
                "task_id": execution.task_id,
                "task_status": execution.task_status,
                "created_at": datetime.now(UTC).isoformat(),
                "definition_node": node,
                "incoming_edges": incoming_edges,
            }
        )
    payload["execution_attempts"] = attempts


def latest_canvas_execution_attempt(
    db: Session,
    user: User,
    run_id: str,
    node_id: str,
) -> dict | None:
    task_and_payload = _canvas_run_task(db, user, run_id)
    if task_and_payload is None:
        return None
    attempts = task_and_payload[1].get("execution_attempts") or []
    failed = [
        item
        for item in attempts
        if isinstance(item, dict)
        and item.get("node_id") == node_id
        and item.get("status") in {"blocked", "cancelled", "failed"}
    ]
    return failed[-1] if failed else None


def save_canvas_execution_response(
    db: Session,
    user: User,
    run_id: str,
    response: ProductionCanvasSkillExecuteResponse,
    *,
    definition_state: ProductionCanvasSavedState | None = None,
    definition_mode: str = "current",
) -> bool:
    task_and_payload = _canvas_run_task(
        db, user, run_id, capability="execute", for_update=True
    )
    if task_and_payload is None:
        return False
    task, payload = task_and_payload
    executions = _response_executions(response)
    raw_state = payload.get("saved_state")
    if definition_state is None and isinstance(raw_state, dict):
        definition_state = ProductionCanvasSavedState.model_validate(raw_state)
    _append_execution_attempts(payload, executions, definition_state, definition_mode)
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
            node["execution_input_fingerprint"] = execution.input_fingerprint

    task.parameters = json.dumps(payload, ensure_ascii=False)
    db.commit()
    return True
