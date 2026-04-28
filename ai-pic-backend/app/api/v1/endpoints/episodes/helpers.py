"""
Episode helper functions.

Shared utilities for episode operations including validation,
data parsing, and database query helpers.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.script import Episode, Story
from app.models.task import Task
from app.models.user import User
from app.repositories.episode_repository import (
    find_accessible_episode,
    find_accessible_story,
)
from app.schemas.generation import EpisodeStepOutlineModel
from app.schemas.story_structure import StoryStepOutlineCreate
from app.services.episode.episode_scene_normalization import ensure_scenes
from app.utils.json_utils import extract_json_block
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session


def not_deleted(query, model):
    """Filter out soft-deleted rows."""
    return query.filter(model.is_deleted.is_(False))


def get_episode_by_identifier(
    db: Session,
    episode_id: Optional[int],
    episode_business_id: Optional[str],
    current_user: User,
) -> Episode:
    """Get episode by business ID or primary key with ownership check."""
    if not episode_business_id and not episode_id:
        raise HTTPException(status_code=400, detail="episode identifier missing")
    episode = find_accessible_episode(
        db,
        episode_id=episode_id,
        episode_business_id=episode_business_id,
        current_user=current_user,
    )
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")
    return episode


def get_story_by_identifier(
    db: Session,
    story_id: Optional[int],
    story_business_id: Optional[str],
    current_user: User,
) -> Story:
    """Get story by business ID or primary key with ownership check."""
    if not story_business_id and not story_id:
        raise HTTPException(status_code=400, detail="story identifier missing")
    story = find_accessible_story(
        db,
        story_id=story_id,
        story_business_id=story_business_id,
        current_user=current_user,
    )
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    return story


def is_episode_payload_valid(episode_data: Dict[str, Any]) -> bool:
    """Ensure minimal episode payload validity before persisting."""
    summary = (episode_data.get("summary") or "").strip()
    conflicts = episode_data.get("conflicts")
    if not summary:
        return False
    if not conflicts or not isinstance(conflicts, list):
        return False
    return any(isinstance(c, dict) for c in conflicts)


def parse_step_outlines(
    raw_step_outlines: Any, episode_count: int
) -> Optional[Dict[str, Any]]:
    """Parse and validate step outlines from AI generation result."""
    parsed = (
        extract_json_block(raw_step_outlines)
        if isinstance(raw_step_outlines, str)
        else (raw_step_outlines if isinstance(raw_step_outlines, dict) else None)
    )
    if not parsed:
        return None
    try:
        validated = EpisodeStepOutlineModel.model_validate(parsed)
    except ValidationError:
        return None

    outlines = validated.model_dump()
    episodes = []
    for ep in sorted(
        outlines.get("episodes", []),
        key=lambda item: item.get("episode_number") or 0,
    ):
        logline = (ep.get("logline") or "").strip()
        if not logline:
            continue
        item = {
            "episode_number": ep.get("episode_number"),
            "title": ep.get("title"),
            "logline": logline,
        }
        if ep.get("beats"):
            item["beats"] = ep["beats"]
        episodes.append(item)
    if not episodes:
        return None
    outlines["episodes"] = episodes[:episode_count]
    return outlines


def persist_story_outlines(
    story: Story,
    outlines: Dict[str, Any],
    *,
    prompt: Optional[str],
    agent_run: Dict[str, Any],
) -> None:
    """Persist step outlines to story extra_metadata."""
    existing_meta = (
        dict(story.extra_metadata) if isinstance(story.extra_metadata, dict) else {}
    )
    outline_payload = {
        "episodes": outlines.get("episodes", []),
        "prompt": prompt,
        "agent_run": agent_run or None,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    existing_meta["episode_step_outlines"] = outline_payload
    story.extra_metadata = existing_meta


def build_outline_rows(
    *,
    outlines: Dict[str, Any],
    treatment,
    story: Story,
    episode_id_map: Dict[int, int],
    agent_run: Dict[str, Any],
) -> List[StoryStepOutlineCreate]:
    """Build StoryStepOutlineCreate rows from parsed outlines."""
    outline_rows: list[StoryStepOutlineCreate] = []
    for outline in outlines.get("episodes", []):
        ep_number = outline.get("episode_number")
        episode_id = episode_id_map.get(ep_number)
        if not episode_id:
            continue
        beats = outline.get("beats") or []
        for beat_idx, beat in enumerate(beats, start=1):
            if not isinstance(beat, dict):
                continue
            outline_rows.append(
                StoryStepOutlineCreate(
                    story_id=story.id,
                    story_treatment_id=treatment.id,
                    episode_id=episode_id,
                    sequence_number=beat.get("sequence_number") or beat_idx,
                    act_label=beat.get("act_label"),
                    beat_title=beat.get("beat_title") or f"Beat {beat_idx}",
                    beat_summary=beat.get("beat_summary")
                    or beat.get("description")
                    or f"情节点 {beat_idx}",
                    dramatic_question=beat.get("dramatic_question"),
                    characters_involved=beat.get("characters_involved"),
                    location_hint=beat.get("location_hint"),
                    duration_estimate_minutes=beat.get("duration_estimate_minutes"),
                    status="draft",
                    metadata={
                        "source": agent_run.get("generation_method"),
                        "agent_reasoning": agent_run.get("reasoning"),
                    },
                )
            )
    return outline_rows


def build_stub_episodes_from_outlines(
    outlines: Optional[Dict[str, Any]], episode_count: int
) -> list[Dict[str, Any]]:
    """Build stub episode drafts from outlines when AI content parsing fails."""
    if not outlines:
        return []
    episodes: list[Dict[str, Any]] = []
    for idx, outline in enumerate(
        outlines.get("episodes", [])[:episode_count], start=1
    ):
        logline = (outline.get("logline") or "").strip()
        if not logline:
            continue
        ep_number = outline.get("episode_number") or idx
        title = outline.get("title") or f"第{ep_number}集"
        episodes.append(
            {
                "episode_number": ep_number,
                "title": title,
                "summary": logline,
                "plot_points": [],
                "character_arcs": None,
                "conflicts": [
                    {
                        "description": logline,
                        "intensity": "medium",
                    }
                ],
                "scene_count": None,
            }
        )
    return episodes


def update_task_progress(db: Session, task: Optional[Task], description: str) -> None:
    """Update task progress description."""
    if not task:
        return
    task.description = description
    db.commit()
