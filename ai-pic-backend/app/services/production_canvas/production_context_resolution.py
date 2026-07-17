from __future__ import annotations

from dataclasses import dataclass

from app.models.user import User
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.schemas.production_canvas_content import (
    ProductionCanvasPlanningDraft,
    ProductionCanvasProductionContext,
)
from app.services.production_canvas.asset_selection import CanvasAssetSelection
from app.services.production_canvas.content_provisioning import provision_canvas_content
from app.services.production_canvas.context_resolution import resolve_canvas_plan
from app.services.production_canvas.production_context_assets import asset_associations
from app.services.production_canvas.production_context_questions import (
    add_asset_questions,
    add_missing_protagonist_question,
    add_story_question,
)
from app.services.production_canvas.production_context_request import (
    apply_context_answers,
    apply_persisted_spec,
)
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class ResolvedProductionContext:
    request: ProductionCanvasPlanRequest
    assets: CanvasAssetSelection
    context: ProductionCanvasProductionContext


def resolve_production_context(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
    planning: ProductionCanvasPlanningDraft,
) -> ResolvedProductionContext:
    answered_request = apply_context_answers(request)
    enriched = answered_request.model_copy(
        update={"prompt": _asset_query(answered_request.prompt, planning)}
    )
    initial = resolve_canvas_plan(
        db,
        user,
        enriched,
        allow_provisioning=False,
        asset_intent=planning.brief.assets,
        focus_episode_number=planning.brief.video_spec.focus_episode_number,
        asset_policy=planning.brief.assets.asset_policy,
    )
    planning = apply_persisted_spec(db, user, planning, initial.request)
    planning = add_asset_questions(planning, initial.assets, answered_request)
    planning = add_story_question(
        db,
        user,
        planning,
        answered_request,
        initial.request,
    )
    planning = add_missing_protagonist_question(
        planning,
        answered_request,
        initial.request,
    )
    if planning.brief.ready_for_execution:
        resolved = resolve_canvas_plan(
            db,
            user,
            enriched,
            allow_provisioning=True,
            asset_intent=planning.brief.assets,
            focus_episode_number=planning.brief.video_spec.focus_episode_number,
            asset_policy=planning.brief.assets.asset_policy,
        )
    else:
        resolved = initial
    resolved_request = resolved.request.model_copy(
        update={
            "prompt": request.prompt,
            "brief_overrides": request.brief_overrides,
            "clarification_answers": request.clarification_answers,
        }
    )
    provisioned = provision_canvas_content(
        db,
        user,
        resolved_request,
        planning,
        resolved.assets,
    )
    context = ProductionCanvasProductionContext(
        brief=planning.brief,
        content_plan=planning.content_plan,
        asset_associations=asset_associations(planning, resolved.assets),
        selected_asset_ids=resolved.assets.outputs(),
        created_story_ids=provisioned.created_story_ids,
        created_episode_ids=provisioned.created_episode_ids,
    )
    return ResolvedProductionContext(
        request=provisioned.request,
        assets=resolved.assets,
        context=context,
    )


def _asset_query(
    prompt: str,
    planning: ProductionCanvasPlanningDraft,
) -> str:
    assets = planning.brief.assets
    lines = [prompt]
    if assets.virtual_ip_name:
        lines.append(f"以{assets.virtual_ip_name}为主角。")
    for environment in assets.environment_names:
        lines.append(f"以{environment}为场景。")
    if planning.content_plan.title:
        lines.append(f"故事标题：{planning.content_plan.title}。")
    return "\n".join(lines)
