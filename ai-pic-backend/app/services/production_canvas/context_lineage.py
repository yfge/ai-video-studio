from __future__ import annotations

from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.repositories.environment_repository import EnvironmentRepository
from app.repositories.production_canvas_context_repository import (
    ProductionCanvasContextRepository,
)
from app.repositories.script_repository import (
    EpisodeRepository,
    ScriptRepository,
    StoryRepository,
)
from app.repositories.task_repository import TaskRepository
from app.repositories.timeline_repository import TimelineRepository
from app.repositories.virtual_ip_environment_repository import (
    VirtualIPEnvironmentRepository,
)
from app.repositories.virtual_ip_repository import VirtualIPRepository
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from sqlalchemy.orm import Session


def _owner_id(user: User) -> int | None:
    return None if user.is_admin or user.is_superuser else int(user.id)


def _validate_lineage(
    name: str,
    actual: int | None,
    requested: int | None,
) -> None:
    if requested is not None and actual != requested:
        raise ValidationError(f"{name} 与上游业务上下文不一致", field=name)


def _timeline_has_clip(timeline, clip_id: str) -> bool:
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    return any(
        isinstance(clip, dict) and str(clip.get("clip_id")) == clip_id
        for track in spec.get("tracks") or []
        if isinstance(track, dict)
        for clip in track.get("clips") or []
    )


def validate_story_ip(
    db: Session,
    request: ProductionCanvasPlanRequest,
) -> None:
    if request.story_id is None or request.virtual_ip_id is None:
        return
    linked_ids = ProductionCanvasContextRepository(db).list_story_virtual_ip_ids(
        request.story_id
    )
    if request.virtual_ip_id not in linked_ids:
        raise ValidationError(
            "virtual_ip_id 与 story_id 的角色归属不一致",
            field="virtual_ip_id",
        )


def validate_ip_environment(
    db: Session,
    request: ProductionCanvasPlanRequest,
) -> None:
    if request.virtual_ip_id is None or request.environment_id is None:
        return
    linked = VirtualIPEnvironmentRepository(db).get_pair(
        virtual_ip_id=request.virtual_ip_id,
        environment_id=request.environment_id,
    )
    if linked is None:
        raise ValidationError(
            "environment_id 不属于指定 virtual_ip_id 的环境资源池",
            field="environment_id",
        )


def resolve_explicit_lineage(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanRequest:
    updates: dict[str, int] = {}
    owner_id = _owner_id(user)
    if request.timeline_id is not None:
        timeline = TimelineRepository(db).get_accessible(request.timeline_id, owner_id)
        if timeline is None:
            raise NotFoundError("Timeline", request.timeline_id)
        _validate_lineage(
            "timeline_version",
            timeline.version,
            request.timeline_version,
        )
        _validate_lineage("script_id", timeline.script_id, request.script_id)
        _validate_lineage("episode_id", timeline.episode_id, request.episode_id)
        updates.update(
            timeline_version=int(timeline.version),
            script_id=int(timeline.script_id),
            episode_id=int(timeline.episode_id),
        )
    script_id = request.script_id or updates.get("script_id")
    if script_id is not None:
        script = ScriptRepository(db).get_with_relations(
            script_id=script_id,
            user_id=owner_id,
        )
        if script is None:
            raise NotFoundError.script(script_id)
        _validate_lineage("episode_id", script.episode_id, request.episode_id)
        updates.update(
            script_id=int(script.id),
            episode_id=int(script.episode_id),
            story_id=int(script.episode.story_id),
        )
    episode_id = request.episode_id or updates.get("episode_id")
    if episode_id is not None:
        episode = EpisodeRepository(db).get_with_story(
            episode_id=episode_id,
            user_id=owner_id,
        )
        if episode is None:
            raise NotFoundError.episode(episode_id)
        _validate_lineage("story_id", episode.story_id, request.story_id)
        updates.update(episode_id=int(episode.id), story_id=int(episode.story_id))
    story_id = request.story_id or updates.get("story_id")
    if story_id is not None:
        story = StoryRepository(db).get_by_user(story_id, owner_id)
        if story is None:
            raise NotFoundError.story(story_id)
        updates["story_id"] = int(story.id)
    if request.virtual_ip_id is not None:
        VirtualIPRepository(db).get_owned_by_id(request.virtual_ip_id, user)
    if request.environment_id is not None:
        EnvironmentRepository(db).get_owned_by_identifier(request.environment_id, user)
    if (
        request.task_id is not None
        and TaskRepository(db).get_user_task(
            task_id=request.task_id,
            user_id=int(user.id),
        )
        is None
    ):
        raise NotFoundError("Task", request.task_id)
    resolved = request.model_copy(update=updates)
    validate_story_ip(db, resolved)
    validate_ip_environment(db, resolved)
    return resolved


def bind_latest_timeline(
    db: Session,
    request: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanRequest:
    if request.timeline_id is not None:
        return request
    if request.script_id is None:
        if request.timeline_version is not None or request.clip_id is not None:
            raise ValidationError(
                "timeline_version/clip_id 需要 timeline_id 或 script_id",
                field="timeline_id",
            )
        return request
    timeline = TimelineRepository(db).get_latest_for_episode_script(
        episode_id=int(request.episode_id),
        script_id=int(request.script_id),
    )
    if timeline is None:
        if request.timeline_version is not None or request.clip_id is not None:
            raise ValidationError(
                "当前剧本尚无可绑定的 Timeline",
                field="timeline_id",
            )
        return request
    _validate_lineage("timeline_version", timeline.version, request.timeline_version)
    return request.model_copy(
        update={
            "timeline_id": int(timeline.id),
            "timeline_version": int(timeline.version),
        }
    )


def validate_resolved_clip(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
) -> None:
    if request.clip_id is None:
        return
    if request.timeline_id is None:
        raise ValidationError("clip_id 需要 timeline_id", field="timeline_id")
    timeline = TimelineRepository(db).get_accessible(
        request.timeline_id,
        _owner_id(user),
    )
    if timeline is None:
        raise NotFoundError("Timeline", request.timeline_id)
    if not _timeline_has_clip(timeline, request.clip_id):
        raise ValidationError("clip_id 不属于指定 Timeline", field="clip_id")
