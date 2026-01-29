"""
Script utilities for data transformation and normalization.

Provides helper functions for building story/episode data structures,
normalizing AI-generated content, and extracting script structure.
"""

from typing import Any, Dict, List

from app.core.validators.character_registry import preferred_display_name
from app.models.script import Episode, Story
from app.utils.marketing_meta import merge_marketing_meta
from sqlalchemy.orm import Session

from .scene_utils import extract_episode_scenes


def collect_previous_episode_summaries(
    db: Session,
    story_id: int,
    current_episode_number: int,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """
    Collect previous episode summaries for context.

    Args:
        db: Database session
        story_id: Story ID
        current_episode_number: Current episode number
        limit: Max episodes to include

    Returns:
        List of episode summary dicts
    """
    if current_episode_number <= 1:
        return []

    previous_episodes = (
        db.query(Episode)
        .filter(
            Episode.story_id == story_id,
            Episode.episode_number < current_episode_number,
        )
        .order_by(Episode.episode_number.desc())
        .limit(limit)
        .all()
    )

    summaries: List[Dict[str, Any]] = []
    for ep in reversed(previous_episodes):
        summaries.append(
            {
                "episode_number": ep.episode_number,
                "title": ep.title,
                "summary": ep.summary or "",
                "plot_points": ep.plot_points or [],
                "conflicts": ep.conflicts or [],
            }
        )
    return summaries


def build_character_profiles(story: Story) -> List[Dict[str, Any]]:
    """
    Build character profiles from story data.

    Args:
        story: Story model instance

    Returns:
        List of character profile dicts
    """
    profiles: Dict[str, Dict[str, Any]] = {}

    def _ensure_profile(name: str) -> Dict[str, Any]:
        return profiles.setdefault(name, {"name": name})

    story_characters = getattr(story, "story_characters", []) or []
    has_registry = any(
        getattr(sc, "is_deleted", False) is False for sc in story_characters
    )
    if not has_registry:
        # Legacy fallback: use story.main_characters when no StoryCharacter registry exists.
        main_chars = (
            story.main_characters if isinstance(story.main_characters, list) else []
        )
        for raw in main_chars:
            if isinstance(raw, dict):
                name = raw.get("name") or raw.get("character_name") or raw.get("id")
                if not name:
                    continue
                profile = _ensure_profile(str(name))
                profile.setdefault(
                    "role",
                    raw.get("role") or raw.get("type") or raw.get("role_type"),
                )
                profile.setdefault(
                    "description", raw.get("description") or raw.get("summary")
                )
                profile.setdefault(
                    "personality", raw.get("personality") or raw.get("traits")
                )
                profile.setdefault(
                    "motivation", raw.get("motivation") or raw.get("goal")
                )
                profile.setdefault("arc", raw.get("arc") or raw.get("character_arc"))
            elif isinstance(raw, str):
                profile = _ensure_profile(raw)
                profile.setdefault("description", "主要角色")

    # Process StoryCharacter registry (single source of truth when present).
    for sc in story_characters:
        if getattr(sc, "is_deleted", False):
            continue
        name = getattr(sc, "character_name", None)
        vip = getattr(sc, "virtual_ip", None)
        if not name and vip:
            name = preferred_display_name(getattr(vip, "name", None)) or getattr(
                vip, "name", None
            )
        if not name:
            continue
        profile = _ensure_profile(str(name))
        profile.setdefault("role", getattr(sc, "role_type", None))
        profile.setdefault("description", getattr(sc, "background", None))
        profile.setdefault("personality", getattr(sc, "personality", None))
        profile.setdefault("motivation", getattr(sc, "motivation", None))
        profile.setdefault("arc", getattr(sc, "character_arc", None))
        relationships = getattr(sc, "relationships", None)
        if relationships and not profile.get("relationships"):
            profile["relationships"] = relationships
        if vip:
            vip_desc = getattr(vip, "description", None)
            if vip_desc and not profile.get("description"):
                profile["description"] = vip_desc

    # Clean and return profiles
    return [
        {k: v for k, v in profile.items() if v not in (None, "", [], {}, set())}
        for profile in profiles.values()
    ]


def build_episode_data(episode: Episode) -> Dict[str, Any]:
    """
    Build episode data dict for prompt generation.

    Args:
        episode: Episode model instance

    Returns:
        Episode data dict
    """
    scenes = extract_episode_scenes(episode)
    scene_count = episode.scene_count or (len(scenes) if scenes else None)
    marketing_meta = merge_marketing_meta(
        episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {},
        (
            episode.generation_params
            if isinstance(episode.generation_params, dict)
            else {}
        ),
    )
    return {
        "episode_number": episode.episode_number,
        "title": episode.title,
        "summary": episode.summary,
        "plot_points": episode.plot_points,
        "character_arcs": episode.character_arcs,
        "conflicts": episode.conflicts,
        "duration_minutes": episode.duration_minutes,
        "scene_count": scene_count,
        "scenes": scenes,
        **marketing_meta,
    }


def build_story_data(
    story: Story,
    *,
    previous_episode_summaries: List[Dict[str, Any]],
    character_profiles: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build story data dict for prompt generation.

    Args:
        story: Story model instance
        previous_episode_summaries: Previous episode summaries
        character_profiles: Character profiles

    Returns:
        Story data dict
    """
    extra_meta = story.extra_metadata if isinstance(story.extra_metadata, dict) else {}
    marketing_meta = merge_marketing_meta(
        extra_meta,
        story.generation_params if isinstance(story.generation_params, dict) else {},
    )
    return {
        "title": story.title,
        "story_format": getattr(story, "story_format", None),
        "genre": story.genre,
        "theme": story.theme,
        "synopsis": story.synopsis,
        "main_conflict": story.main_conflict,
        "resolution": story.resolution,
        "main_characters": story.main_characters,
        "character_relationships": story.character_relationships,
        "world_building": story.world_building,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location,
        "previous_episode_summaries": previous_episode_summaries,
        "character_profiles": character_profiles,
        "continuity_ledger": (
            extra_meta.get("continuity_ledger")
            if isinstance(extra_meta.get("continuity_ledger"), dict)
            else None
        ),
        **marketing_meta,
    }
