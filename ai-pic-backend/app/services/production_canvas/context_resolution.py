from __future__ import annotations

from dataclasses import dataclass

from app.models.user import User
from app.repositories.production_canvas_context_repository import (
    ProductionCanvasContextRepository,
)
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.schemas.production_canvas_brief import ProductionCanvasAssetIntent
from app.services.production_canvas.asset_provisioning import (
    provision_missing_canvas_assets,
)
from app.services.production_canvas.asset_selection import (
    CanvasAssetSelection,
    select_canvas_assets,
)
from app.services.production_canvas.context_lineage import (
    bind_latest_timeline,
    resolve_explicit_lineage,
    validate_ip_environment,
    validate_resolved_clip,
    validate_story_ip,
)
from app.services.production_canvas.context_prompt_resolution import (
    derive_story_ip,
    resolve_prompt_story_episode,
    selected_asset_context,
)
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class ResolvedCanvasPlan:
    request: ProductionCanvasPlanRequest
    assets: CanvasAssetSelection


def resolve_canvas_plan(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
    *,
    allow_provisioning: bool = True,
    asset_intent: ProductionCanvasAssetIntent | None = None,
    focus_episode_number: int | None = None,
    asset_policy: str = "reuse_preferred",
) -> ResolvedCanvasPlan:
    resolved = resolve_explicit_lineage(db, user, request)
    story_ip_id = derive_story_ip(db, user, resolved)
    if story_ip_id is not None:
        resolved = resolved.model_copy(update={"virtual_ip_id": story_ip_id})
    assets = select_canvas_assets(db, user, resolved)
    resolved = selected_asset_context(resolved, assets)
    resolved = resolve_prompt_story_episode(
        db,
        user,
        resolved,
        episode_number=focus_episode_number,
    )
    resolved = _defer_unlinked_inferred_ip(db, request, resolved)
    validate_story_ip(db, resolved)
    story_ip_id = derive_story_ip(db, user, resolved)
    if story_ip_id is not None and story_ip_id != resolved.virtual_ip_id:
        updates: dict[str, int | None] = {"virtual_ip_id": story_ip_id}
        if request.environment_id is None:
            updates["environment_id"] = None
        resolved = resolved.model_copy(update=updates)
        assets = select_canvas_assets(db, user, resolved)
        resolved = selected_asset_context(resolved, assets)
        resolved = _defer_unlinked_inferred_ip(db, request, resolved)
    validate_story_ip(db, resolved)
    validate_ip_environment(db, resolved)
    resolved = bind_latest_timeline(db, resolved)
    validate_resolved_clip(db, user, resolved)
    if allow_provisioning:
        resolved, assets = provision_missing_canvas_assets(
            db,
            user,
            resolved,
            assets,
            asset_intent=asset_intent,
            explicit_environment_id=request.environment_id,
            asset_policy=asset_policy,
        )
        resolved = _defer_unlinked_inferred_ip(db, request, resolved)
    validate_story_ip(db, resolved)
    validate_ip_environment(db, resolved)
    return ResolvedCanvasPlan(request=resolved, assets=assets)


def _defer_unlinked_inferred_ip(
    db: Session,
    original: ProductionCanvasPlanRequest,
    resolved: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanRequest:
    if (
        original.virtual_ip_id is not None
        or resolved.story_id is None
        or resolved.virtual_ip_id is None
    ):
        return resolved
    linked_ids = ProductionCanvasContextRepository(db).list_story_virtual_ip_ids(
        int(resolved.story_id)
    )
    if int(resolved.virtual_ip_id) in linked_ids:
        return resolved
    return resolved.model_copy(update={"virtual_ip_id": None})
