from __future__ import annotations

from app.prompts.manager import PromptManager
from app.prompts.templates import PromptTemplate
from app.schemas.generation_requests import StoryGenerationRequest


def build_story_outline_preview_prompt(request: StoryGenerationRequest) -> str:
    characters = [
        {"id": char_id, "name": f"角色#{char_id}", "description": ""}
        for char_id in request.character_ids
    ]
    variables = {
        "title": request.title,
        "story_format": request.story_format,
        "genre": request.genre,
        "characters": characters,
        "market_region": request.market_region,
        "micro_genre": request.micro_genre,
        "pacing_template": request.pacing_template,
        "hook_plan": request.hook_plan.model_dump() if request.hook_plan else None,
        "twist_density": request.twist_density,
        "cliffhanger_plan": request.cliffhanger_plan or [],
        "ad_snippets": (
            [snippet.model_dump() for snippet in request.ad_snippets]
            if request.ad_snippets
            else []
        ),
        "theme": request.theme,
        "target_audience": request.target_audience,
        "duration_minutes": request.duration_minutes,
        "setting_time": request.setting_time,
        "setting_location": request.setting_location,
        "world_building": request.world_building,
        "additional_requirements": request.additional_requirements,
        "style_preferences": request.style_preferences or [],
        "content_restrictions": request.content_restrictions or [],
    }
    return PromptManager().render_prompt(PromptTemplate.STORY_OUTLINE.value, variables)
