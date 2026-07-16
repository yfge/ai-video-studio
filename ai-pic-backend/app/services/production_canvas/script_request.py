from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.script_repository import EpisodeRepository
from app.schemas.generation_requests import ScriptGenerationRequest
from app.schemas.production_canvas import ProductionCanvasSkillExecuteRequest
from app.services.single_video_generation import build_single_video_script_request


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
        duration_minutes=int(
            episode.duration_minutes or episode.story.duration_minutes or 3
        ),
        aspect_ratio=(
            episode.aspect_ratio or episode.story.default_aspect_ratio or "9:16"
        ),
        style=episode.story.theme,
    )
