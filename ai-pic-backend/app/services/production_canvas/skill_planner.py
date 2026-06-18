from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasPlanRequest,
    ProductionCanvasPlanResponse,
    ProductionCanvasSkillManifest,
)
from app.services.production_canvas.asset_selection import select_canvas_assets
from app.services.production_canvas.nodes import build_plan_nodes
from app.services.production_canvas.runner import build_canvas_skill_results
from app.services.production_canvas.skills import list_canvas_skill_definitions


def build_canvas_skill_plan(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanResponse:
    asset_selection = select_canvas_assets(db, user, request)
    skill_results = build_canvas_skill_results(request, asset_selection)
    manifest = ProductionCanvasSkillManifest(
        version="production_canvas.v1",
        entry_skill="production_canvas.create",
        skills=list_canvas_skill_definitions(),
        reuse_policy="backend_reuses_existing_services_and_tasks",
    )
    return ProductionCanvasPlanResponse(
        prompt=request.prompt,
        skill_manifest=manifest,
        selected_assets=asset_selection.selected,
        skill_results=skill_results,
        nodes=build_plan_nodes(skill_results),
    )
