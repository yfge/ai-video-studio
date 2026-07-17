from __future__ import annotations

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.script_repository import EpisodeRepository
from app.schemas.generation_requests import ScriptGenerationRequest
from app.schemas.production_canvas import ProductionCanvasSkillExecuteRequest
from app.services.production_canvas.script_context_compiler import (
    compile_canvas_script_context,
)
from app.services.single_video_generation import build_single_video_script_request
from sqlalchemy.orm import Session


def build_canvas_script_generation_request(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> ScriptGenerationRequest:
    episode = EpisodeRepository(db).get_with_story(
        episode_id=int(request.episode_id),
        user_id=int(user.id),
    )
    if episode is None:
        raise NotFoundError.episode(int(request.episode_id))
    metadata = (
        episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
    )
    if request.production_context is not None:
        compiled = compile_canvas_script_context(
            request.production_context,
            episode_number=int(episode.episode_number),
        )
        return ScriptGenerationRequest(
            episode_id=int(episode.id),
            generation_mode="production",
            auto_timeline_pipeline=True,
            target_chars_per_episode=compiled.target_chars,
            additional_requirements=compiled.requirements,
            style_preferences=compiled.style_preferences,
            model=compiled.model,
        )
    if (
        request.planning_mode != "single_video"
        and episode.story.genre != "single_video"
        and metadata.get("creation_mode") != "single_video"
    ):
        return ScriptGenerationRequest(
            episode_id=int(episode.id),
            generation_mode="production",
            auto_timeline_pipeline=True,
            additional_requirements=request.prompt,
        )
    return build_single_video_script_request(
        episode_id=int(episode.id),
        prompt=request.prompt,
        duration_seconds=_single_video_duration_seconds(episode, metadata),
        aspect_ratio=(
            episode.aspect_ratio or episode.story.default_aspect_ratio or "9:16"
        ),
        style=episode.story.theme,
    )


def _single_video_duration_seconds(episode, metadata: dict) -> int:
    brief = metadata.get("brief")
    if isinstance(brief, dict):
        value = brief.get("duration_seconds")
        if isinstance(value, int) and value > 0:
            return value
    return int((episode.duration_minutes or episode.story.duration_minutes or 3) * 60)
