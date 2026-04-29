from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from app.models.script import Story
from app.schemas.generation import EpisodeStepOutlineModel
from app.schemas.story_structure import StoryStepOutlineCreate
from app.utils.json_utils import extract_json_block
from pydantic import ValidationError


def not_deleted(query, model):
    return query.filter(model.is_deleted.is_(False))


def build_agent_run_info(result: Dict[str, Any]) -> Dict[str, Any]:
    """Build an audit payload from ai_service result for agent_run persistence."""
    if not isinstance(result, dict):
        return {}
    payload: Dict[str, Any] = {
        "generation_method": result.get("generation_method"),
        "template_used": result.get("template_used"),
        "provider_used": result.get("provider_used"),
        "model_used": result.get("model_used"),
        "usage": result.get("usage"),
        "reasoning": result.get("reasoning"),
    }

    raw_content = result.get("content")
    if isinstance(raw_content, str) and raw_content.strip():
        payload["raw_content"] = raw_content
    normalized = result.get("normalized")
    if isinstance(normalized, dict) and normalized:
        payload["normalized"] = normalized
    validation_errors = result.get("validation_errors")
    if validation_errors:
        payload["validation_errors"] = validation_errors
    repair_attempts = result.get("repair_attempts")
    if repair_attempts:
        payload["repair_attempts"] = repair_attempts
    first_attempt = result.get("first_attempt")
    if first_attempt:
        payload["first_attempt"] = first_attempt
    quality_gate = result.get("quality_gate")
    if quality_gate:
        payload["quality_gate"] = quality_gate

    return {k: v for k, v in payload.items() if v is not None}


def is_episode_payload_valid(episode_data: Dict[str, Any]) -> bool:
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
    episodes: list[dict] = []
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
    existing_meta = (
        dict(story.extra_metadata) if isinstance(story.extra_metadata, dict) else {}
    )
    existing_meta["episode_step_outlines"] = {
        "episodes": outlines.get("episodes", []),
        "prompt": prompt,
        "agent_run": agent_run or None,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    story.extra_metadata = existing_meta


def build_stub_episodes_from_outlines(
    outlines: Optional[Dict[str, Any]], episode_count: int
) -> list[Dict[str, Any]]:
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
                "conflicts": [{"description": logline, "intensity": "medium"}],
                "scene_count": None,
            }
        )
    return episodes


def build_step_outline_rows(
    *,
    outlines: Dict[str, Any],
    treatment: Any,
    story_id: int,
    episode_id_map: Dict[int, int],
    agent_run: Dict[str, Any],
) -> list[StoryStepOutlineCreate]:
    rows: list[StoryStepOutlineCreate] = []
    for outline in outlines.get("episodes", []):
        ep_number = outline.get("episode_number")
        episode_id = episode_id_map.get(ep_number)
        if not episode_id:
            continue
        beats = outline.get("beats") or []
        for beat_idx, beat in enumerate(beats, start=1):
            if not isinstance(beat, dict):
                continue
            rows.append(
                StoryStepOutlineCreate(
                    story_id=story_id,
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
    return rows
