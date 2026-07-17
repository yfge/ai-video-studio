from __future__ import annotations

from app.models.user import User
from app.repositories.script_repository import EpisodeRepository
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.schemas.production_canvas_brief import ProductionCanvasBriefConflict
from app.schemas.production_canvas_content import ProductionCanvasPlanningDraft
from sqlalchemy.orm import Session


def apply_context_answers(
    request: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanRequest:
    updates = {}
    aliases = {
        "virtual_ip_id": ("context.virtual_ip_id", "asset.virtual_ip_id"),
        "environment_id": ("context.environment_id", "asset.environment_id"),
        "story_id": ("context.story_id",),
        "episode_id": ("context.episode_id",),
    }
    for field, keys in aliases.items():
        value = next(
            (
                request.clarification_answers.get(key)
                for key in keys
                if request.clarification_answers.get(key)
            ),
            None,
        )
        if value and value.isdigit():
            updates[field] = int(value)
    return request.model_copy(update=updates) if updates else request


def apply_persisted_spec(
    db: Session,
    user: User,
    planning: ProductionCanvasPlanningDraft,
    request: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanningDraft:
    if request.episode_id is None:
        return planning
    episode = EpisodeRepository(db).get_with_story(
        episode_id=int(request.episode_id),
        user_id=int(user.id),
    )
    if episode is None:
        return planning
    brief = planning.brief.model_copy(deep=True)
    spec = brief.video_spec.model_copy(deep=True)
    conflicts = list(brief.conflicts)
    persisted_duration = persisted_duration_seconds(episode)
    if spec.duration_seconds is None and persisted_duration:
        spec.duration_seconds = persisted_duration
    elif (
        persisted_duration
        and spec.duration_seconds
        and persisted_duration != spec.duration_seconds
    ):
        conflicts.append(
            ProductionCanvasBriefConflict(
                field="video_spec.duration_seconds",
                prompt_value=str(spec.duration_seconds),
                authoritative_value=str(persisted_duration),
                resolution="user_prompt_overrides_persisted_spec",
                reason="本次明确生产目标优先于历史默认规格，并保留冲突证据。",
            )
        )
    persisted_ratio = episode.aspect_ratio or episode.story.default_aspect_ratio
    if spec.aspect_ratio is None and persisted_ratio in {"9:16", "16:9"}:
        spec.aspect_ratio = persisted_ratio
    return planning.model_copy(
        update={
            "brief": brief.model_copy(
                update={"video_spec": spec, "conflicts": conflicts}
            )
        }
    )


def persisted_duration_seconds(episode) -> int | None:
    metadata = (
        episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
    )
    brief = metadata.get("production_brief") or metadata.get("brief")
    if isinstance(brief, dict):
        video_spec = (
            brief.get("video_spec")
            if isinstance(brief.get("video_spec"), dict)
            else brief
        )
        value = video_spec.get("duration_seconds")
        if isinstance(value, int) and value > 0:
            return value
    minutes = episode.duration_minutes or episode.story.duration_minutes
    return int(minutes * 60) if minutes else None
