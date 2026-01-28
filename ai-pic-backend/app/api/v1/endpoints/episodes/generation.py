"""
Episode generation endpoints.

AI-powered episode generation from story data.
"""

from __future__ import annotations

from typing import List

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.context_pack import ContextPackBudget, StoryContextPack
from app.schemas.context_pack_preview import EpisodeContextPackPreviewRequest
from app.schemas.generation_requests import EpisodeGenerationRequest
from app.schemas.script import EpisodeResponse
from app.services.context_pack.story_context_pack_builder import (
    build_story_context_pack,
)
from app.services.episode.episode_generation_service import EpisodeGenerationService
from app.utils.marketing_meta import apply_marketing_overrides, merge_marketing_meta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Backward-compat export for tests/legacy callers (they monkeypatch this name).
ai_service = None  # type: ignore[assignment]

router = APIRouter()


@router.post("/generate", response_model=List[EpisodeResponse])
async def generate_episodes(
    request: EpisodeGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate episodes using AI."""
    service = EpisodeGenerationService(db, current_user)
    created = await service.generate_episodes(request)
    return [EpisodeResponse.from_orm(episode) for episode in created]


@router.post("/prompt/preview")
async def preview_episode_prompt(
    request: EpisodeGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return the final prompt for episode generation (without calling model)."""
    service = EpisodeGenerationService(db, current_user)
    prompt = service.build_preview_prompt(request)
    return {"success": True, "data": {"prompt": prompt}}


@router.post("/context-pack/preview", response_model=StoryContextPack)
async def preview_episode_context_pack(
    request: EpisodeContextPackPreviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return the Context Pack used for episode generation (without calling model)."""
    story = EpisodeGenerationService(db, current_user)._get_story(request.story_id)

    generation_params = (
        story.generation_params if isinstance(story.generation_params, dict) else None
    )
    extra_meta = story.extra_metadata if isinstance(story.extra_metadata, dict) else {}
    continuity_ledger = (
        extra_meta.get("continuity_ledger")
        if isinstance(extra_meta.get("continuity_ledger"), dict)
        else None
    )
    marketing_meta = merge_marketing_meta(extra_meta, generation_params or {})

    story_snapshot = {
        "title": story.title,
        "story_format": getattr(story, "story_format", None),
        "genre": story.genre,
        "premise": story.premise,
        "synopsis": story.synopsis,
        "main_conflict": story.main_conflict,
        "resolution": story.resolution,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location,
        "world_building": story.world_building,
        "character_relationships": story.character_relationships,
        "default_aspect_ratio": getattr(story, "default_aspect_ratio", None),
        **marketing_meta,
    }

    hook_plan_payload = request.hook_plan.model_dump() if request.hook_plan else None
    ad_snippets_payload = (
        [item.model_dump() for item in request.ad_snippets]
        if request.ad_snippets
        else None
    )
    apply_marketing_overrides(
        story_snapshot,
        {
            "market_region": request.market_region,
            "micro_genre": request.micro_genre,
            "pacing_template": request.pacing_template,
            "hook_plan": hook_plan_payload,
            "twist_density": request.twist_density,
            "cliffhanger_plan": request.cliffhanger_plan,
            "ad_snippets": ad_snippets_payload,
        },
    )

    budget = request.budget or ContextPackBudget()
    budget_overrides = budget.model_dump()
    if not request.include_character_cards:
        budget_overrides["max_character_cards"] = 0
    if not request.include_recent_episodes:
        budget_overrides["max_recent_episode_summaries"] = 0
    budget = ContextPackBudget(**budget_overrides)

    pack = build_story_context_pack(
        db=db,
        story_id=story.id,
        story_snapshot=story_snapshot,
        continuity_ledger=(
            continuity_ledger if request.include_continuity_ledger else None
        ),
        generation_params=generation_params,
        budget=budget,
    )
    return StoryContextPack.model_validate(pack)
