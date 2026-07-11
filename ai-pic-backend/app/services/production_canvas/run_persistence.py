from __future__ import annotations

import json

from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasExecutionAttempt,
    ProductionCanvasPlanRequest,
    ProductionCanvasPlanResponse,
    ProductionCanvasRunResponse,
    ProductionCanvasSavedState,
    ProductionCanvasSkillResult,
)
from app.schemas.production_canvas_collaboration import CanvasAccessRole
from app.services.production_canvas.nodes import build_plan_nodes
from app.services.production_canvas.skills import list_canvas_skill_definitions
from app.services.production_canvas.stale_runtime import apply_canvas_stale_state
from sqlalchemy.orm import Session

from .access_control import CanvasCapability, canvas_access_role, canvas_run_access


def _run_context(payload: dict) -> dict:
    keys = {"episode_id", "script_id", "timeline_id", "timeline_version"}
    context = {
        key: value
        for key, value in (payload.get("requested_asset_ids") or {}).items()
        if key in keys and value is not None
    }
    sources = list(payload.get("skill_results") or [])
    saved_state = payload.get("saved_state") or {}
    sources.extend(saved_state.get("nodes") or [])
    for source in sources:
        outputs = source.get("outputs") if isinstance(source, dict) else None
        if not isinstance(outputs, dict):
            continue
        context.update(
            {key: outputs[key] for key in keys if outputs.get(key) is not None}
        )
    return context


def _current_run_payload(payload: dict) -> dict:
    definitions = list_canvas_skill_definitions()
    existing = {
        item.get("skill"): ProductionCanvasSkillResult.model_validate(item)
        for item in payload.get("skill_results") or []
        if isinstance(item, dict) and item.get("skill")
    }
    context = _run_context(payload)
    results: list[ProductionCanvasSkillResult] = []
    for skill in definitions:
        result = existing.get(skill.id)
        if result is not None:
            results.append(result)
            continue
        required_inputs = [] if context.get("script_id") else ["script_id"]
        outputs = dict(context)
        if required_inputs:
            outputs["required_inputs"] = required_inputs
        results.append(
            ProductionCanvasSkillResult(
                skill=skill.id,
                label=skill.label,
                status="review" if not required_inputs else "blocked",
                title=skill.description,
                detail=(
                    "人工触发后复用当前 Timeline 版本。"
                    if not required_inputs
                    else "需要先绑定 script_id。"
                ),
                outputs=outputs,
                reuse_targets=skill.reuse_targets,
            )
        )
    current = dict(payload)
    manifest = dict(current.get("skill_manifest") or {})
    manifest["skills"] = [item.model_dump() for item in definitions]
    current["skill_manifest"] = manifest
    current["skill_results"] = [item.model_dump() for item in results]
    current["nodes"] = [item.model_dump() for item in build_plan_nodes(results)]
    return current


def _run_response_from_task(
    task: Task,
    payload: dict,
    access_role: CanvasAccessRole = "owner",
) -> ProductionCanvasRunResponse | None:
    saved_state = None
    raw_saved_state = payload.get("saved_state")
    if isinstance(raw_saved_state, dict):
        saved_state = ProductionCanvasSavedState.model_validate(raw_saved_state)

    plan = ProductionCanvasPlanResponse.model_validate(_current_run_payload(payload))
    data = plan.model_dump()
    data.update(
        {
            "run_id": task.business_id,
            "task_id": task.id,
            "access_role": access_role,
            "saved_state": saved_state,
            "execution_attempts": [
                ProductionCanvasExecutionAttempt.model_validate(item)
                for item in payload.get("execution_attempts") or []
                if isinstance(item, dict)
            ],
        }
    )
    return ProductionCanvasRunResponse(**data)


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
    return _run_response_from_task(task, payload, role or "owner")


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


def save_canvas_state(
    db: Session,
    user: User,
    run_id: str,
    state: ProductionCanvasSavedState,
    *,
    capability: CanvasCapability = "edit",
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
    state = apply_canvas_stale_state(previous, state)
    payload["saved_state"] = state.model_dump(by_alias=True, mode="json")
    task.parameters = json.dumps(payload, ensure_ascii=False)
    db.commit()
    db.refresh(task)
    role = canvas_access_role(task, payload, user)
    return _run_response_from_task(task, payload, role or "owner")


def save_canvas_client_state(
    db: Session,
    user: User,
    run_id: str,
    state: ProductionCanvasSavedState,
) -> ProductionCanvasRunResponse | None:
    from .client_state_merge import merge_canvas_client_state

    previous = load_canvas_saved_state(db, user, run_id)
    return save_canvas_state(
        db, user, run_id, merge_canvas_client_state(previous, state)
    )
