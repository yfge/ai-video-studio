"""
Script utilities for data transformation and normalization.

Provides helper functions for building story/episode data structures,
normalizing AI-generated content, and extracting script structure.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.script import Episode, Story
from app.utils.marketing_meta import merge_marketing_meta


def to_int(value: Any) -> Optional[int]:
    """Safely convert value to int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
        summaries.append({
            "episode_number": ep.episode_number,
            "title": ep.title,
            "summary": ep.summary or "",
            "plot_points": ep.plot_points or [],
            "conflicts": ep.conflicts or [],
        })
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

    # Process main characters
    main_chars = story.main_characters if isinstance(story.main_characters, list) else []
    for raw in main_chars:
        if isinstance(raw, dict):
            name = raw.get("name") or raw.get("character_name") or raw.get("id")
            if not name:
                continue
            profile = _ensure_profile(str(name))
            profile.setdefault("role", raw.get("role") or raw.get("type") or raw.get("role_type"))
            profile.setdefault("description", raw.get("description") or raw.get("summary"))
            profile.setdefault("personality", raw.get("personality") or raw.get("traits"))
            profile.setdefault("motivation", raw.get("motivation") or raw.get("goal"))
            profile.setdefault("arc", raw.get("arc") or raw.get("character_arc"))
        elif isinstance(raw, str):
            profile = _ensure_profile(raw)
            profile.setdefault("description", "主要角色")

    # Process story characters
    story_characters = getattr(story, "story_characters", []) or []
    for sc in story_characters:
        name = getattr(sc, "character_name", None)
        if not name and getattr(sc, "virtual_ip", None):
            name = getattr(sc.virtual_ip, "name", None)
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
        if getattr(sc, "virtual_ip", None):
            vip_desc = getattr(sc.virtual_ip, "description", None)
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
        episode.generation_params if isinstance(episode.generation_params, dict) else {},
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


def extract_episode_scenes(episode: Episode) -> List[Dict[str, Any]]:
    """
    Extract scenes from episode metadata.

    Args:
        episode: Episode model instance

    Returns:
        List of scene dicts
    """
    if not episode:
        return []

    meta = episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
    scenes_src = meta.get("scenes") if isinstance(meta, dict) else []
    if not isinstance(scenes_src, list):
        return []

    cleaned: List[Dict[str, Any]] = []
    for idx, raw in enumerate(scenes_src, start=1):
        if not isinstance(raw, dict):
            continue
        base = dict(raw)
        scene_no = to_int(base.get("scene_number")) or idx
        base["scene_number"] = scene_no
        summary = base.get("summary") or base.get("description") or base.get("beat_summary")
        location = base.get("location") or base.get("place") or base.get("setting")
        time_of_day = base.get("time_of_day") or base.get("time")

        if summary:
            base.setdefault("summary", summary)
            base.setdefault("description", summary)
        if location:
            base.setdefault("location", location)
        if time_of_day:
            base.setdefault("time_of_day", time_of_day)
        if not base.get("slug_line"):
            if location and time_of_day:
                base["slug_line"] = f"{location} - {time_of_day}"
            elif summary:
                base["slug_line"] = str(summary)[:80]
            else:
                base["slug_line"] = f"Scene {scene_no}"
        cleaned.append(base)

    return cleaned


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
    marketing_meta = merge_marketing_meta(
        story.extra_metadata if isinstance(story.extra_metadata, dict) else {},
        story.generation_params if isinstance(story.generation_params, dict) else {},
    )
    return {
        "title": story.title,
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
        **marketing_meta,
    }
