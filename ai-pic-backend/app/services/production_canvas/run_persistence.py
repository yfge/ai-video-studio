from __future__ import annotations

import json
from datetime import UTC, datetime

from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasPlanRequest,
    ProductionCanvasPlanResponse,
    ProductionCanvasRunResponse,
    ProductionCanvasSavedState,
)
from app.services.production_canvas.stale_runtime import apply_canvas_stale_state
from sqlalchemy.orm import Session

from .access_control import CanvasCapability, canvas_access_role, canvas_run_access
from .definition_activity import record_definition_change
from .run_context import canvas_run_context
from .run_response import run_response_from_task


def _canvas_run_task(
    db: Session,
    user: User,
    run_id: str,
    *,
    capability: CanvasCapability = "view",
    for_update: bool = False,
) -> tuple[Task, dict] | None:
    access = canvas_run_access(db, user, run_id, capability, for_update=for_update)
    return (access[0], access[1]) if access else None


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
            "requested_asset_ids": plan.resolved_context.model_dump(),
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


def load_canvas_skill_run(
    db: Session,
    user: User,
    run_id: str,
) -> ProductionCanvasRunResponse | None:
    task_and_payload = _canvas_run_task(db, user, run_id)
    if task_and_payload is None:
        return None
    task, payload = task_and_payload
    role = canvas_access_role(task, payload, user)
    return run_response_from_task(task, payload, role or "owner")


def load_canvas_saved_state(
    db: Session,
    user: User,
    run_id: str,
) -> ProductionCanvasSavedState | None:
    task_and_payload = _canvas_run_task(db, user, run_id)
    if task_and_payload is None:
        return None
    _, payload = task_and_payload
    raw_state = payload.get("saved_state")
    if not isinstance(raw_state, dict):
        return None
    return ProductionCanvasSavedState.model_validate(raw_state)


def _save_canvas_state(
    db: Session,
    user: User,
    run_id: str,
    state: ProductionCanvasSavedState,
    *,
    capability: CanvasCapability = "edit",
    merge_client_state: bool = False,
    authoritative_context: dict | None = None,
) -> ProductionCanvasRunResponse | None:
    task_and_payload = _canvas_run_task(
        db, user, run_id, capability=capability, for_update=True
    )
    if task_and_payload is None:
        return None
    task, payload = task_and_payload
    previous = None
    if isinstance(payload.get("saved_state"), dict):
        previous = ProductionCanvasSavedState.model_validate(payload["saved_state"])
    client_context_revision = state.resolved_context_revision
    server_context_revision = int(payload.get("resolved_context_revision") or 0)
    terminal_task_context = None
    if merge_client_state:
        from .run_task_context import reconcile_canvas_terminal_task_context

        terminal_task_context = reconcile_canvas_terminal_task_context(
            db, user, payload, previous or state
        )
        if terminal_task_context is not None:
            payload["resolved_context"] = terminal_task_context
    protect_execution_context = bool(
        merge_client_state
        and (
            client_context_revision < server_context_revision
            or terminal_task_context is not None
        )
    )
    stale_client_state = protect_execution_context
    if merge_client_state:
        from .client_state_merge import (
            canvas_client_state_has_stale_runtime,
            merge_canvas_client_state,
        )

        stale_client_state = protect_execution_context or (
            canvas_client_state_has_stale_runtime(previous, state)
        )
        state = merge_canvas_client_state(
            previous,
            state,
            (payload.get("resolved_context") if stale_client_state else None),
        )
    state = apply_canvas_stale_state(previous, state)
    if record_definition_change(payload, user, run_id, previous, state):
        payload["saved_state_updated_by"] = user.id
        payload["saved_state_updated_at"] = datetime.now(UTC).isoformat()
    payload["saved_state"] = state.model_dump(by_alias=True, mode="json")
    if authoritative_context is not None:
        payload["resolved_context"] = canvas_run_context(
            {"resolved_context": authoritative_context}
        )
    elif stale_client_state and isinstance(payload.get("resolved_context"), dict):
        payload["resolved_context"] = canvas_run_context(
            {"resolved_context": payload["resolved_context"]}
        )
    else:
        context_payload = dict(payload)
        context_payload.pop("resolved_context", None)
        payload["resolved_context"] = canvas_run_context(context_payload)
    state = state.model_copy(
        update={
            "resolved_context_revision": int(
                payload.get("resolved_context_revision") or 0
            )
        }
    )
    payload["saved_state"] = state.model_dump(by_alias=True, mode="json")
    task.parameters = json.dumps(payload, ensure_ascii=False)
    db.commit()
    db.refresh(task)
    role = canvas_access_role(task, payload, user)
    return run_response_from_task(task, payload, role or "owner")


def save_canvas_state(
    db: Session,
    user: User,
    run_id: str,
    state: ProductionCanvasSavedState,
    *,
    capability: CanvasCapability = "edit",
    authoritative_context: dict | None = None,
) -> ProductionCanvasRunResponse | None:
    return _save_canvas_state(
        db,
        user,
        run_id,
        state,
        capability=capability,
        authoritative_context=authoritative_context,
    )


def save_canvas_client_state(
    db: Session,
    user: User,
    run_id: str,
    state: ProductionCanvasSavedState,
) -> ProductionCanvasRunResponse | None:
    return _save_canvas_state(db, user, run_id, state, merge_client_state=True)
