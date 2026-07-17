from __future__ import annotations

from app.models.script import Story
from app.models.user import User
from app.repositories.script_repository import EpisodeRepository, StoryRepository
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.schemas.production_canvas_content import ProductionCanvasPlanningDraft
from app.services.production_canvas.asset_selection import CanvasAssetSelection
from app.services.production_canvas.content_provisioning_contract import (
    CanvasContentProvisioning,
)
from app.services.production_canvas.content_provisioning_models import (
    create_episode,
    create_story,
    ensure_story_character,
)
from app.services.production_canvas.single_video_content_provisioning import (
    sync_single_video_content,
)
from sqlalchemy.orm import Session


def provision_canvas_content(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
    planning: ProductionCanvasPlanningDraft,
    assets: CanvasAssetSelection,
) -> CanvasContentProvisioning:
    if not planning.brief.ready_for_execution:
        return CanvasContentProvisioning(request, [], [])
    if request.planning_mode == "single_video":
        return sync_single_video_content(db, user, request, planning, assets)

    story = _load_story(db, user, request.story_id)
    created_story_ids: list[int] = []
    created_episode_ids: list[int] = []
    try:
        if story is not None and request.episode_id is not None:
            virtual_ip = (
                assets.selected.virtual_ips[0] if assets.selected.virtual_ips else None
            )
            if virtual_ip:
                ensure_story_character(db, story, virtual_ip)
                db.commit()
            return CanvasContentProvisioning(request, [], [])
        if story is None:
            story = create_story(db, user, planning)
            db.flush()
            created_story_ids.append(int(story.id))
        virtual_ip = (
            assets.selected.virtual_ips[0] if assets.selected.virtual_ips else None
        )
        if virtual_ip:
            ensure_story_character(db, story, virtual_ip)
        episodes = EpisodeRepository(db).list_by_story(
            int(story.id),
            user_id=_owner_id(user),
        )
        by_number = {int(item.episode_number): item for item in episodes}
        requested_plans = planning.content_plan.episodes[:24]
        for episode_plan in requested_plans:
            if episode_plan.episode_number in by_number:
                continue
            episode = create_episode(story, planning, episode_plan)
            db.add(episode)
            db.flush()
            by_number[int(episode.episode_number)] = episode
            created_episode_ids.append(int(episode.id))
        focus_number = planning.brief.video_spec.focus_episode_number or (
            requested_plans[0].episode_number if requested_plans else 1
        )
        focus = by_number.get(int(focus_number))
        if focus is None and by_number:
            focus = by_number[min(by_number)]
        db.commit()
        if created_story_ids:
            db.refresh(story)
        for episode_id in created_episode_ids:
            episode = next(
                item for item in by_number.values() if int(item.id) == episode_id
            )
            db.refresh(episode)
        updates = {
            "story_id": int(story.id),
            **({"virtual_ip_id": int(virtual_ip.id)} if virtual_ip is not None else {}),
        }
        if focus is not None:
            updates["episode_id"] = int(focus.id)
        return CanvasContentProvisioning(
            request.model_copy(update=updates),
            created_story_ids,
            created_episode_ids,
        )
    except Exception:
        db.rollback()
        raise


def _load_story(db: Session, user: User, story_id: int | None) -> Story | None:
    if story_id is None:
        return None
    return StoryRepository(db).get_by_user(story_id, user_id=_owner_id(user))


def _owner_id(user: User) -> int | None:
    return None if user.is_admin or user.is_superuser else int(user.id)
