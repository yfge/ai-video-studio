from __future__ import annotations

from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasPlanRequest,
    ProductionCanvasPlanResponse,
    ProductionCanvasResolvedContext,
    ProductionCanvasSkillManifest,
)
from app.services.production_canvas.context_resolution import resolve_canvas_plan
from app.services.production_canvas.nodes import build_plan_nodes
from app.services.production_canvas.runner import build_canvas_skill_results
from app.services.production_canvas.skills import list_canvas_skill_definitions
from sqlalchemy.orm import Session


def build_canvas_skill_plan(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanResponse:
    resolved = resolve_canvas_plan(db, user, request)
    skill_results = build_canvas_skill_results(resolved.request, resolved.assets)
    manifest = ProductionCanvasSkillManifest(
        version="production_canvas.v1",
        entry_skill="production_canvas.create",
        skills=list_canvas_skill_definitions(),
        reuse_policy="backend_reuses_existing_services_and_tasks",
    )
    return ProductionCanvasPlanResponse(
        prompt=resolved.request.prompt,
        resolved_context=ProductionCanvasResolvedContext.model_validate(
            resolved.request.model_dump(exclude={"prompt"})
        ),
        skill_manifest=manifest,
        selected_assets=resolved.assets.selected,
        skill_results=skill_results,
        nodes=build_plan_nodes(skill_results),
    )
