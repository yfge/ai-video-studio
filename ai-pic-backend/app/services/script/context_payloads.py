"""Prompt context payload builders for script generation."""

from __future__ import annotations

from typing import Any, Dict, List

from app.models.script import Episode, Story
from app.services.script.scene_utils import extract_episode_scenes
from app.services.script.script_utils import (
    collect_previous_episode_summaries as _collect_previous_episode_summaries,
)
from app.utils.marketing_meta import merge_marketing_meta


def collect_previous_episode_summaries(
    db,
    story_id: int,
    current_episode_number: int,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    return _collect_previous_episode_summaries(
        db,
        story_id,
        current_episode_number,
        limit=limit,
    )


def build_character_profiles(story: Story) -> List[Dict[str, Any]]:
    """Build character profiles from story metadata and registered characters."""
    profiles: Dict[str, Dict[str, Any]] = {}

    def _ensure_profile(name: str) -> Dict[str, Any]:
        return profiles.setdefault(name, {"name": name})

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
                "role", raw.get("role") or raw.get("type") or raw.get("role_type")
            )
            profile.setdefault(
                "description", raw.get("description") or raw.get("summary")
            )
            profile.setdefault(
                "personality", raw.get("personality") or raw.get("traits")
            )
            profile.setdefault("motivation", raw.get("motivation") or raw.get("goal"))
            profile.setdefault("arc", raw.get("arc") or raw.get("character_arc"))
        elif isinstance(raw, str):
            profile = _ensure_profile(raw)
            profile.setdefault("description", "主要角色")

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

    return [
        {k: v for k, v in profile.items() if v not in (None, "", [], {}, set())}
        for profile in profiles.values()
    ]


def build_episode_data(episode: Episode) -> Dict[str, Any]:
    """Build episode context data for script generation prompts."""
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
        "story_format": getattr(getattr(episode, "story", None), "story_format", None),
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
    """Build story context data for script generation prompts."""
    marketing_meta = merge_marketing_meta(
        story.extra_metadata if isinstance(story.extra_metadata, dict) else {},
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
        **marketing_meta,
    }
