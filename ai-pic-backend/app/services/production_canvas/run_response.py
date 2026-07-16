from __future__ import annotations

from app.models.task import Task
from app.schemas.production_canvas import (
    ProductionCanvasExecutionAttempt,
    ProductionCanvasPlanResponse,
    ProductionCanvasRunResponse,
    ProductionCanvasSavedState,
    ProductionCanvasSkillResult,
)
from app.schemas.production_canvas_collaboration import CanvasAccessRole

from .autonomous_planner import deterministic_canvas_planner_decision
from .nodes import build_plan_nodes
from .run_context import canvas_run_context, merge_canvas_node_context_outputs
from .skills import list_canvas_skill_definitions


def _current_run_payload(payload: dict) -> dict:
    definitions = list_canvas_skill_definitions()
    definition_by_id = {item.id: item for item in definitions}
    existing = {
        item.get("skill"): ProductionCanvasSkillResult.model_validate(item)
        for item in payload.get("skill_results") or []
        if isinstance(item, dict) and item.get("skill")
    }
    planner = payload.get("planner")
    selected_skills = (
        planner.get("selected_skills")
        if isinstance(planner, dict)
        and isinstance(planner.get("selected_skills"), list)
        else [item.id for item in definitions]
    )
    selected_definitions = [
        definition_by_id[skill]
        for skill in selected_skills
        if skill in definition_by_id
    ]
    context = canvas_run_context(payload)
    results: list[ProductionCanvasSkillResult] = []
    for skill in selected_definitions:
        result = existing.get(skill.id)
        if result is not None:
            results.append(
                result.model_copy(
                    update={
                        "outputs": merge_canvas_node_context_outputs(
                            {"skill": result.skill, "outputs": result.outputs},
                            context,
                            authoritative=True,
                        )
                    }
                )
            )
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
    if not isinstance(planner, dict):
        fallback = deterministic_canvas_planner_decision(
            str(current.get("prompt") or "恢复生产画布"),
            reason="legacy_run",
        )
        current["planner"] = fallback.evidence.model_dump()
        current.setdefault(
            "edges",
            [edge.model_dump() for edge in fallback.edges],
        )
    current["resolved_context"] = context
    return current


def run_response_from_task(
    task: Task,
    payload: dict,
    access_role: CanvasAccessRole = "owner",
) -> ProductionCanvasRunResponse:
    saved_state = None
    raw_saved_state = payload.get("saved_state")
    if isinstance(raw_saved_state, dict):
        saved_state = ProductionCanvasSavedState.model_validate(
            {
                **raw_saved_state,
                "resolved_context_revision": int(
                    payload.get("resolved_context_revision") or 0
                ),
            }
        )
    plan = ProductionCanvasPlanResponse.model_validate(_current_run_payload(payload))
    response = plan.model_dump()
    response.update(
        run_id=task.business_id,
        task_id=task.id,
        access_role=access_role,
        saved_state=saved_state,
        execution_attempts=[
            ProductionCanvasExecutionAttempt.model_validate(item)
            for item in payload.get("execution_attempts") or []
            if isinstance(item, dict)
        ],
    )
    return ProductionCanvasRunResponse.model_validate(response)
