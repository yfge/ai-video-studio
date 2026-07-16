from __future__ import annotations

from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasPlanRequest,
    ProductionCanvasPlanResponse,
    ProductionCanvasResolvedContext,
    ProductionCanvasSkillManifest,
)
from app.services.production_canvas.nodes import build_plan_nodes
from app.services.production_canvas.production_context_builder import (
    build_deterministic_production_planning_draft,
    build_production_planning_draft,
)
from app.services.production_canvas.production_context_resolution import (
    resolve_production_context,
)
from app.services.production_canvas.runner import build_canvas_skill_results
from app.services.production_canvas.skills import list_canvas_skill_definitions
from sqlalchemy.orm import Session

from .autonomous_planner import (
    CanvasPlannerDecision,
    deterministic_canvas_planner_decision,
    plan_canvas_skills,
)
from .planner_ports import CANONICAL_MANIFEST_VERSION


def _manifest() -> ProductionCanvasSkillManifest:
    return ProductionCanvasSkillManifest(
        version=CANONICAL_MANIFEST_VERSION,
        entry_skill="production_canvas.create",
        skills=list_canvas_skill_definitions(),
        reuse_policy="backend_reuses_existing_services_and_tasks",
    )


def _plan_response(resolved, decision: CanvasPlannerDecision):
    manifest = _manifest()
    all_results = build_canvas_skill_results(
        resolved.request,
        resolved.assets,
        resolved.context,
    )
    by_skill = {result.skill: result for result in all_results}
    skill_results = [
        by_skill[skill] for skill in decision.selected_skills if skill in by_skill
    ]
    return ProductionCanvasPlanResponse(
        prompt=resolved.request.prompt,
        resolved_context=ProductionCanvasResolvedContext.model_validate(
            resolved.request.model_dump(exclude={"prompt", "planning_mode"})
        ),
        skill_manifest=manifest,
        selected_assets=resolved.assets.selected,
        production_context=resolved.context,
        skill_results=skill_results,
        nodes=build_plan_nodes(
            skill_results,
            manifest_version=manifest.version,
        ),
        edges=decision.edges,
        planner=decision.evidence,
    )


def build_canvas_skill_plan(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanResponse:
    planning = build_deterministic_production_planning_draft(request)
    resolved = resolve_production_context(db, user, request, planning)
    return _plan_response(
        resolved,
        deterministic_canvas_planner_decision(
            resolved.request.prompt,
            reason="deterministic_builder",
        ),
    )


async def build_autonomous_canvas_skill_plan(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanResponse:
    planning = await build_production_planning_draft(request)
    resolved = resolve_production_context(db, user, request, planning)
    context = ProductionCanvasResolvedContext.model_validate(
        resolved.request.model_dump(exclude={"prompt", "planning_mode"})
    )
    decision = await plan_canvas_skills(
        prompt=resolved.request.prompt,
        resolved_context=context,
        selected_assets=resolved.assets.selected,
        production_context=resolved.context,
    )
    return _plan_response(resolved, decision)
