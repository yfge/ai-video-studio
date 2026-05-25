"""Script prompt preview endpoints."""

from __future__ import annotations

from typing import Any, Dict

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.prompts.manager import PromptManager
from app.prompts.templates import PromptTemplate
from app.repositories.scripts_route_repository import ScriptsRouteRepository
from app.schemas.generation_requests import ScriptGenerationRequest
from app.services.script.context_payloads import (
    build_character_profiles,
    build_episode_data,
    build_story_data,
    collect_previous_episode_summaries,
)
from app.utils.marketing_meta import apply_marketing_overrides
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/prompt/preview")
async def preview_script_prompt(
    request: ScriptGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    episode = ScriptsRouteRepository(db).get_prompt_preview_episode(
        episode_id=request.episode_id,
        current_user=current_user,
    )
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")

    story = episode.story
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    previous_episode_summaries = collect_previous_episode_summaries(
        db, story.id, episode.episode_number
    )
    character_profiles = build_character_profiles(story)
    episode_data = build_episode_data(episode)
    story_data = build_story_data(
        story,
        previous_episode_summaries=previous_episode_summaries,
        character_profiles=character_profiles,
    )
    marketing_overrides = _build_marketing_overrides(request)
    apply_marketing_overrides(story_data, marketing_overrides)
    apply_marketing_overrides(episode_data, marketing_overrides)
    variables = {
        "story": story_data,
        "episode": episode_data,
        "format_type": request.format_type,
        "language": request.language,
        "dialogue_style": request.dialogue_style,
        "scene_detail_level": request.scene_detail_level,
        "template_style": request.template_style,
        "target_chars_per_episode": request.target_chars_per_episode,
        "quality_threshold": request.quality_threshold,
        "additional_requirements": request.additional_requirements,
        "style_preferences": request.style_preferences or [],
    }
    prompt = PromptManager().render_prompt(
        PromptTemplate.SCRIPT_GENERATION.value, variables
    )
    return {"success": True, "data": {"prompt": prompt}}


def _build_marketing_overrides(request: ScriptGenerationRequest) -> Dict[str, Any]:
    hook_plan_payload = request.hook_plan.model_dump() if request.hook_plan else None
    ad_snippets_payload = (
        [snippet.model_dump() for snippet in request.ad_snippets]
        if request.ad_snippets
        else None
    )
    return {
        "market_region": request.market_region,
        "micro_genre": request.micro_genre,
        "hook_plan": hook_plan_payload,
        "twist_density": request.twist_density,
        "cliffhanger_plan": request.cliffhanger_plan,
        "ad_snippets": ad_snippets_payload,
    }
