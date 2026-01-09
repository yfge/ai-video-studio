from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.script import Episode, Story, StoryCharacter

from .story_novel_export_utils import clip_text


def _not_deleted(query, model):
    return query.filter(model.is_deleted.is_(False))


def _load_episode_summaries(db: Session, *, story_id: int, limit: int = 30) -> list[dict[str, Any]]:
    episodes = (
        _not_deleted(db.query(Episode), Episode)
        .filter(Episode.story_id == story_id)
        .order_by(Episode.episode_number.asc())
        .limit(limit)
        .all()
    )
    result: list[dict[str, Any]] = []
    for ep in episodes:
        result.append(
            {
                "episode_number": ep.episode_number,
                "title": ep.title,
                "summary": clip_text(ep.summary, 1200),
                "plot_points": ep.plot_points,
            }
        )
    return result


def _load_story_character_profiles(
    db: Session, *, story_id: int, limit: int = 50
) -> list[dict[str, Any]]:
    rows = (
        _not_deleted(db.query(StoryCharacter), StoryCharacter)
        .filter(StoryCharacter.story_id == story_id)
        .options(joinedload(StoryCharacter.virtual_ip))
        .limit(limit)
        .all()
    )

    result: list[dict[str, Any]] = []
    for row in rows:
        vip = row.virtual_ip
        vip_payload: dict[str, Any] | None = None
        if vip and not getattr(vip, "is_deleted", False):
            vip_payload = {
                "id": vip.id,
                "business_id": getattr(vip, "business_id", None),
                "name": vip.name,
                "description": clip_text(vip.description, 800),
                "tags": vip.tags,
                "background_story": clip_text(vip.background_story, 1500),
                "biography": clip_text(getattr(vip, "biography", None), 2000),
            }

        result.append(
            {
                "story_character_id": row.id,
                "virtual_ip_id": row.virtual_ip_id,
                "virtual_ip_business_id": row.virtual_ip_business_id,
                "name": row.character_name or (vip.name if vip else None),
                "role_type": row.role_type,
                "importance": row.importance,
                "personality": clip_text(row.personality, 800),
                "background": clip_text(row.background, 1500),
                "motivation": clip_text(row.motivation, 800),
                "character_arc": clip_text(row.character_arc, 800),
                "relationships": row.relationships,
                "virtual_ip": vip_payload,
            }
        )

    return result


def build_story_novel_payload(db: Session, *, story: Story) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "title": story.title,
        "story_format": getattr(story, "story_format", None),
        "genre": story.genre,
        "theme": story.theme,
        "target_audience": story.target_audience,
        "duration_minutes": story.duration_minutes,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location,
        "world_building": clip_text(story.world_building, 2000),
        "premise": clip_text(story.premise, 1500),
        "synopsis": clip_text(story.synopsis, 4000),
        "main_conflict": clip_text(story.main_conflict, 1500),
        "resolution": clip_text(story.resolution, 1500),
        "main_characters": story.main_characters,
        "character_relationships": story.character_relationships,
        "episodes": _load_episode_summaries(db, story_id=story.id, limit=30),
        "characters": _load_story_character_profiles(db, story_id=story.id, limit=50),
    }
    return payload
