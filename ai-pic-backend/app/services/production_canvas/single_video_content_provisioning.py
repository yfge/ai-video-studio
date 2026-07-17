from __future__ import annotations

import math

from app.models.user import User
from app.repositories.script_repository import EpisodeRepository
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.schemas.production_canvas_content import ProductionCanvasPlanningDraft
from app.schemas.single_video_project import SingleVideoProjectRequest
from app.services.production_canvas.asset_selection import CanvasAssetSelection
from app.services.production_canvas.content_provisioning_contract import (
    CanvasContentProvisioning,
)
from app.services.production_canvas.content_provisioning_models import (
    ensure_story_character,
    planning_metadata,
)
from app.services.single_video_project_service import create_single_video_project
from sqlalchemy.orm import Session


def sync_single_video_content(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
    planning: ProductionCanvasPlanningDraft,
    assets: CanvasAssetSelection,
) -> CanvasContentProvisioning:
    if request.episode_id is None:
        request, created_story_ids, created_episode_ids = _create_project(
            db,
            user,
            request,
            planning,
            assets,
        )
    else:
        created_story_ids = []
        created_episode_ids = []
    episode = EpisodeRepository(db).get_with_story(
        episode_id=int(request.episode_id),
        user_id=int(user.id),
    )
    if episode is None:
        return CanvasContentProvisioning(
            request,
            created_story_ids,
            created_episode_ids,
        )
    virtual_ip = assets.selected.virtual_ips[0] if assets.selected.virtual_ips else None
    if virtual_ip:
        ensure_story_character(db, episode.story, virtual_ip)
    _apply_video_spec(episode, planning)
    metadata = planning_metadata(planning)
    episode.extra_metadata = {
        **(episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}),
        **metadata,
    }
    episode.story.extra_metadata = {
        **(
            episode.story.extra_metadata
            if isinstance(episode.story.extra_metadata, dict)
            else {}
        ),
        **metadata,
    }
    db.commit()
    return CanvasContentProvisioning(
        request.model_copy(
            update=(
                {"virtual_ip_id": int(virtual_ip.id)} if virtual_ip is not None else {}
            )
        ),
        created_story_ids,
        created_episode_ids,
    )


def _create_project(db, user, request, planning, assets):
    spec = planning.brief.video_spec
    project = create_single_video_project(
        db,
        user,
        SingleVideoProjectRequest(
            title=planning.content_plan.title,
            prompt=planning.brief.source_prompt,
            duration_seconds=spec.duration_seconds,
            aspect_ratio=spec.aspect_ratio,
            style=(
                "、".join(spec.visual_style)
                or "、".join(planning.brief.intent.tone)
                or None
            ),
            virtual_ip_id=(
                assets.selected.virtual_ips[0].id
                if assets.selected.virtual_ips
                else None
            ),
            environment_id=(
                assets.selected.environments[0].id
                if assets.selected.environments
                else None
            ),
            start_generation=False,
        ),
    )
    updated = request.model_copy(
        update={
            "story_id": project.story_id,
            "episode_id": project.episode_id,
            **project.context.model_dump(exclude_none=True),
        }
    )
    return updated, [project.story_id], [project.episode_id]


def _apply_video_spec(episode, planning) -> None:
    spec = planning.brief.video_spec
    if spec.duration_seconds:
        duration_minutes = max(1, math.ceil(spec.duration_seconds / 60))
        episode.duration_minutes = duration_minutes
        episode.story.duration_minutes = duration_minutes
    if spec.aspect_ratio:
        episode.aspect_ratio = spec.aspect_ratio
        episode.story.default_aspect_ratio = spec.aspect_ratio
