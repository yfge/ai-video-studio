from __future__ import annotations

from typing import Any, Dict

from app.models.script import Story
from app.prompts.manager import PromptManager
from app.prompts.templates import PromptTemplate
from app.schemas.generation_requests import EpisodeGenerationRequest
from app.services.script.script_utils import build_character_profiles
from app.utils.marketing_meta import merge_marketing_meta


def build_story_data(story: Story) -> Dict[str, Any]:
    extra_meta = story.extra_metadata if isinstance(story.extra_metadata, dict) else {}
    generation_params = (
        story.generation_params if isinstance(story.generation_params, dict) else {}
    )
    marketing_meta = merge_marketing_meta(extra_meta, generation_params)
    return {
        "title": story.title,
        "story_format": getattr(story, "story_format", None),
        "genre": story.genre,
        "theme": story.theme,
        "synopsis": story.synopsis,
        "main_conflict": story.main_conflict,
        "resolution": story.resolution,
        "character_profiles": build_character_profiles(story),
        "main_characters": story.main_characters,
        "character_relationships": story.character_relationships,
        "world_building": story.world_building,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location,
        "continuity_ledger": (
            extra_meta.get("continuity_ledger")
            if isinstance(extra_meta.get("continuity_ledger"), dict)
            else None
        ),
        **marketing_meta,
    }


def build_preview_prompt(
    *,
    request: EpisodeGenerationRequest,
    story_data: Dict[str, Any],
    focus_characters: list[Dict[str, Any]],
) -> str:
    variables = {
        "story": story_data,
        "episode_count": request.episode_count,
        "episode_duration": request.episode_duration,
        "focus_characters": focus_characters,
        "plot_complexity": request.plot_complexity,
        "pacing": request.pacing,
        "additional_requirements": request.additional_requirements,
        "style_preferences": request.style_preferences or [],
    }
    return PromptManager().render_prompt(
        PromptTemplate.EPISODE_GENERATION.value, variables
    )
