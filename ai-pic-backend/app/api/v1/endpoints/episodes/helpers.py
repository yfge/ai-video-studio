"""
Episode helper functions.

Shared utilities for episode operations including validation,
data parsing, and database query helpers.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.script import Story, Episode
from app.models.task import Task
from app.models.user import User
from app.schemas.generation import EpisodeStepOutlineModel
from app.schemas.story_structure import StoryStepOutlineCreate
from app.utils.json_utils import extract_json_block


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
    query = (
        not_deleted(db.query(Episode), Episode)
        .join(Story, Episode.story_id == Story.id)
        .filter(Story.is_deleted.is_(False))
    )
    if episode_business_id:
        query = query.filter(Episode.business_id == episode_business_id)
    elif episode_id:
        query = query.filter(Episode.id == episode_id)
    else:
        raise HTTPException(status_code=400, detail="episode identifier missing")
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(Story.user_id == current_user.id)
    episode = query.first()
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
    query = not_deleted(db.query(Story), Story)
    if story_business_id:
        query = query.filter(Story.business_id == story_business_id)
    elif story_id:
        query = query.filter(Story.id == story_id)
    else:
        raise HTTPException(status_code=400, detail="story identifier missing")
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(Story.user_id == current_user.id)
    story = query.first()
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


def ensure_scenes(ep_data: dict) -> tuple[list[dict], int | None]:
    """Ensure episode data contains usable scenes.

    Note: Some models/schemas may return scenes=[{}, {}, ...].
    This function filters empty objects and auto-fills placeholder scenes
    to avoid unstable frontend display.
    """

    def _as_nonempty_str(value: object | None) -> str | None:
        if not isinstance(value, str):
            return None
        text = value.strip()
        return text or None

    def _to_int(value: object | None) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    raw_scene_count = _to_int(ep_data.get("scene_count"))
    target_scene_count = (
        raw_scene_count if raw_scene_count and raw_scene_count > 0 else None
    )

    raw_scenes = ep_data.get("scenes")
    scenes: list[dict] = []
    if isinstance(raw_scenes, list):
        for idx, raw in enumerate(raw_scenes, start=1):
            if not isinstance(raw, dict):
                continue

            slug_line = _as_nonempty_str(raw.get("slug_line")) or _as_nonempty_str(
                raw.get("title")
            )
            summary = (
                _as_nonempty_str(raw.get("summary"))
                or _as_nonempty_str(raw.get("description"))
                or _as_nonempty_str(raw.get("beat_summary"))
            )
            location = (
                _as_nonempty_str(raw.get("location"))
                or _as_nonempty_str(raw.get("environment"))
                or _as_nonempty_str(raw.get("setting"))
            )
            time_of_day = (
                _as_nonempty_str(raw.get("time_of_day"))
                or _as_nonempty_str(raw.get("time"))
                or _as_nonempty_str(raw.get("period"))
            )

            # Empty object / no valid fields => invalid scene, trigger auto-fill
            if not (slug_line or summary or location or time_of_day):
                continue

            scene_number = _to_int(raw.get("scene_number")) or idx
            scenes.append(
                {
                    **raw,
                    "scene_number": scene_number,
                    "slug_line": slug_line or f"SCENE {scene_number} - beat",
                    "summary": summary or "本场景推进剧情。",
                    "time_of_day": time_of_day or "unspecified",
                    "location": location or "unspecified",
                }
            )

    if not scenes:
        plot_points = ep_data.get("plot_points") or []
        if isinstance(plot_points, list) and plot_points:
            for idx, pp in enumerate(plot_points, start=1):
                desc = None
                timing = None
                if isinstance(pp, dict):
                    desc = _as_nonempty_str(pp.get("description"))
                    timing = _as_nonempty_str(pp.get("timing"))
                scenes.append(
                    {
                        "scene_number": idx,
                        "slug_line": f"SCENE {idx} - {timing or 'beat'}",
                        "summary": desc or "本场景推进剧情。",
                        "time_of_day": "unspecified",
                        "location": "unspecified",
                    }
                )
        else:
            scenes.append(
                {
                    "scene_number": 1,
                    "slug_line": "SCENE 1 - beat",
                    "summary": _as_nonempty_str(ep_data.get("summary"))
                    or "本集开篇场景。",
                    "time_of_day": "unspecified",
                    "location": "unspecified",
                }
            )

    # If model provided scene_count, align the count (pad or truncate)
    if target_scene_count:
        scenes = scenes[:target_scene_count]
        while len(scenes) < target_scene_count:
            idx = len(scenes) + 1
            scenes.append(
                {
                    "scene_number": idx,
                    "slug_line": f"SCENE {idx} - beat",
                    "summary": "本场景推进剧情。",
                    "time_of_day": "unspecified",
                    "location": "unspecified",
                }
            )

    # Normalize scene numbers to avoid missing/duplicate causing unstable display
    for idx, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            continue
        if _to_int(scene.get("scene_number")) is None:
            scene["scene_number"] = idx
        scene.setdefault("slug_line", f"SCENE {idx} - beat")
        scene.setdefault("summary", "本场景推进剧情。")
        scene.setdefault("time_of_day", "unspecified")
        scene.setdefault("location", "unspecified")

    scene_count = target_scene_count or (len(scenes) if scenes else None)
    # Write back to ensure downstream uses cleaned/filled scenes
    ep_data["scenes"] = scenes
    if scene_count is not None:
        ep_data["scene_count"] = scene_count
    return scenes, scene_count
