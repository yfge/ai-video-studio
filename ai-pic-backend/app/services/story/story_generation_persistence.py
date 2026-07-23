"""Build the persisted Story record from a generated Story Seed."""

from datetime import datetime
from typing import Any

from app.schemas.generation_requests import StoryGenerationRequest
from app.services.story.story_generation_utils import build_extra_metadata
from app.services.story.story_seed_service import seed_from_generation


def build_story_data(
    request: StoryGenerationRequest,
    ai_content: dict[str, Any],
    result: dict[str, Any],
    agent_run: dict[str, Any],
    user_id: int,
    characters: list[dict[str, Any]],
) -> dict[str, Any]:
    extra_metadata = _extra_metadata(request, ai_content, agent_run)
    seed = seed_from_generation(ai_content, request, characters)
    return {
        "user_id": user_id,
        "title": request.title,
        "story_format": request.story_format,
        "genre": request.genre,
        "theme": request.theme,
        "target_audience": request.target_audience,
        "duration_minutes": request.duration_minutes,
        "default_aspect_ratio": request.default_aspect_ratio,
        "setting_time": request.setting_time,
        "setting_location": request.setting_location,
        "world_building": request.world_building,
        "premise": seed.premise,
        "synopsis": seed.outline,
        "main_conflict": seed.central_conflict,
        "resolution": seed.ending_direction,
        "main_characters": ai_content.get("main_characters"),
        "character_relationships": ai_content.get("character_relationships"),
        "generation_prompt": result.get("prompt"),
        "ai_model": result.get("generation_method"),
        "generation_params": _generation_params(request),
        "tags": request.tags,
        "workflow_mode": request.workflow_mode,
        "extra_metadata": extra_metadata,
        "status": "draft",
        "story_seed": seed.model_dump(by_alias=True),
        "story_seed_schema": "story_seed_v1",
        "story_seed_status": "draft",
        "story_seed_version": 1,
        "story_seed_updated_at": datetime.utcnow(),
        "memory_mode": (
            "story_scoped_memory_v1"
            if request.workflow_mode == "novel_adaptation_v1"
            else "off"
        ),
        "canon_branch_id": "main",
    }


def _extra_metadata(request, ai_content, agent_run) -> dict:
    metadata = build_extra_metadata(ai_content)
    optional = {
        "market_region": request.market_region,
        "micro_genre": request.micro_genre,
        "pacing_template": request.pacing_template,
        "hook_plan": request.hook_plan.model_dump() if request.hook_plan else None,
        "twist_density": request.twist_density,
        "cliffhanger_plan": request.cliffhanger_plan,
        "ad_snippets": (
            [item.model_dump() for item in request.ad_snippets]
            if request.ad_snippets
            else None
        ),
    }
    for key, value in optional.items():
        if value is not None and key not in metadata:
            metadata[key] = value
    if agent_run:
        metadata["agent_run"] = agent_run
    return metadata


def _generation_params(request) -> dict:
    return {
        "character_ids": request.character_ids,
        "generation_mode": request.generation_mode,
        "story_format": request.story_format,
        "default_aspect_ratio": request.default_aspect_ratio,
        "market_region": request.market_region,
        "micro_genre": request.micro_genre,
        "additional_requirements": request.additional_requirements,
        "style_preferences": request.style_preferences,
        "content_restrictions": request.content_restrictions,
        "model": request.model,
        "temperature": request.temperature or 0.7,
    }
