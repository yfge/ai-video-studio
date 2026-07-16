from __future__ import annotations

import json

from app.models.task import TaskStatus
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.schemas.production_canvas import ProductionCanvasSavedState
from app.services.task_result_context import build_task_result_context
from sqlalchemy.orm import Session

from .run_context import (
    CONTEXT_KEYS,
    canvas_run_context,
    is_scoped_canvas_media,
    merge_canvas_context_outputs,
)


def _parameters(task) -> dict:
    if not task.parameters:
        return {}
    try:
        value = json.loads(task.parameters)
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def reconcile_canvas_terminal_task_context(
    db: Session,
    user: User,
    payload: dict,
    state: ProductionCanvasSavedState,
) -> dict | None:
    """Advance Run context from its latest trusted completed child Tasks."""

    latest_attempts: dict[str, dict] = {}
    for attempt in payload.get("execution_attempts") or []:
        if isinstance(attempt, dict) and isinstance(attempt.get("node_id"), str):
            latest_attempts[attempt["node_id"]] = attempt
    synced = dict(payload.get("resolved_task_context_ids") or {})
    context = canvas_run_context(payload)
    changed = False
    repository = TaskRepository(db)
    for node in state.nodes:
        source = node.model_dump(by_alias=True, mode="json")
        if node.kind == "note" or is_scoped_canvas_media(source):
            continue
        task_id = node.outputs.get("dispatched_task_id")
        if not isinstance(task_id, int) or task_id <= 0:
            continue
        attempt = latest_attempts.get(node.id)
        if not attempt or attempt.get("task_id") != task_id:
            continue
        if synced.get(node.id) == task_id:
            continue
        task = repository.get_user_task(task_id=task_id, user_id=user.id)
        if task is None or task.status != TaskStatus.COMPLETED:
            continue
        result_context = build_task_result_context(
            task_id=task.id,
            parameters=_parameters(task),
            result_file_path=task.result_file_path,
        )
        merged = merge_canvas_context_outputs(context, result_context)
        context = {key: merged[key] for key in CONTEXT_KEYS if key in merged}
        synced[node.id] = task_id
        changed = True
    if not changed:
        return None
    payload["resolved_task_context_ids"] = synced
    payload["resolved_context_revision"] = (
        int(payload.get("resolved_context_revision") or 0) + 1
    )
    return context
