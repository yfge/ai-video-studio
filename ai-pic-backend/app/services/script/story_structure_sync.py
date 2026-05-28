"""Sync script scene payloads into normalized story structure tables."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.models.script import Script
from app.models.story_structure import Scene
from app.schemas.story_structure import SceneBeatCreate, SceneCreate, ShotCreate
from app.services import story_structure_service as story_structure_svc
from app.services.script.scene_utils import to_int
from sqlalchemy.orm import Session


def build_scene_payload_from_script_data(
    scene_raw: Any,
    idx: int,
    script_id: int,
) -> Optional[SceneCreate]:
    """Convert a script scene payload into a normalized scene create schema."""
    if isinstance(scene_raw, dict):
        base = dict(scene_raw)
    elif isinstance(scene_raw, str):
        base = {"summary": scene_raw, "description": scene_raw}
    else:
        return None

    scene_no = to_int(base.get("scene_number")) or idx
    summary = base.get("summary") or base.get("description")
    location = base.get("location") or base.get("place")
    time_of_day = base.get("time_of_day") or base.get("time")

    slug_line = base.get("slug_line")
    if not slug_line:
        if location and time_of_day:
            slug_line = f"{location} - {time_of_day}"
        elif summary:
            slug_line = str(summary)[:80]
        else:
            slug_line = f"Scene {scene_no}"

    estimated_duration = to_int(
        base.get("estimated_duration_seconds")
        or base.get("duration_seconds")
        or base.get("estimated_duration")
    )

    return SceneCreate(
        script_id=script_id,
        scene_number=str(scene_no),
        slug_line=str(slug_line),
        location=location,
        time_of_day=time_of_day,
        summary=summary,
        estimated_duration_seconds=estimated_duration,
        status="draft",
    )


def sync_script_scenes_to_story_structure(
    db: Session,
    script: Script,
    *,
    allow_overwrite: bool = False,
) -> Dict[str, int]:
    """Write script scenes into normalized story structure when absent."""
    logger = get_logger()
    if not script or not script.id:
        return {"created": 0, "beats_created": 0, "shots_created": 0, "skipped": 0}

    existing = story_structure_svc.list_scenes_by_script(db, script.id)
    if existing and not allow_overwrite:
        return {
            "created": 0,
            "beats_created": 0,
            "shots_created": 0,
            "skipped": len(existing),
        }

    if allow_overwrite and existing:
        for scene in existing:
            try:
                story_structure_svc.delete_scene(db, scene.id)
            except Exception as exc:  # pragma: no cover - protective
                logger.warning("failed to delete old normalized scene: %s", exc)

    scenes_src = script.scenes or []
    if not scenes_src and isinstance(script.extra_metadata, dict):
        scenes_src = script.extra_metadata.get("scenes") or []

    created_pairs: list[tuple[Any, Scene]] = []
    seen_numbers: set[str] = set()
    for idx, raw in enumerate(scenes_src, start=1):
        payload = build_scene_payload_from_script_data(raw, idx, script.id)
        if not payload:
            continue
        scene_key = payload.scene_number
        if scene_key in seen_numbers:
            continue
        seen_numbers.add(scene_key)
        try:
            created = story_structure_svc.create_scene(db, payload)
            created_pairs.append((raw, created))
        except Exception as exc:  # pragma: no cover - protective
            logger.warning("failed to write normalized scene %s: %s", scene_key, exc)

    beats_created = 0
    for raw, scene in created_pairs:
        for beat_payload in build_scene_beat_payloads(raw, scene.id):
            try:
                story_structure_svc.create_scene_beat(db, beat_payload)
                beats_created += 1
            except Exception as exc:  # pragma: no cover - protective
                logger.warning(
                    "failed to create normalized beat for scene_id=%s: %s",
                    scene.id,
                    exc,
                )

    shots_created = 0
    for _, scene in created_pairs:
        try:
            story_structure_svc.create_shot(
                db,
                ShotCreate(
                    scene_id=scene.id,
                    shot_number="1",
                    status="planned",
                ),
            )
            shots_created += 1
        except Exception as exc:  # pragma: no cover - protective
            logger.warning(
                "failed to create placeholder shot for scene_id=%s: %s",
                scene.id,
                exc,
            )

    return {
        "created": len(created_pairs),
        "beats_created": beats_created,
        "shots_created": shots_created,
        "skipped": len(existing) if existing and not allow_overwrite else 0,
    }


def build_scene_beat_payloads(scene_raw: Any, scene_id: int) -> list[SceneBeatCreate]:
    if not isinstance(scene_raw, dict):
        return []
    beats = scene_raw.get("beats")
    if not isinstance(beats, list):
        return []
    payloads: list[SceneBeatCreate] = []
    for idx, beat in enumerate(beats, start=1):
        if not isinstance(beat, dict):
            continue
        order_index = to_int(beat.get("order_index")) or idx
        payloads.append(
            SceneBeatCreate(
                scene_id=scene_id,
                order_index=order_index,
                beat_type=beat.get("beat_type"),
                beat_summary=beat.get("visible_event") or beat.get("beat_summary"),
                characters_involved=_characters_involved(beat),
                dialogue_excerpt=_dialogue_excerpt(beat),
                camera_notes=beat.get("camera_notes"),
                duration_seconds=beat.get("duration_seconds"),
                metadata={
                    "dramatic_purpose": beat.get("dramatic_purpose"),
                    "visible_event": beat.get("visible_event"),
                    "hook_tag": beat.get("hook_tag"),
                    "payoff_tag": beat.get("payoff_tag"),
                    "cliffhanger_tag": beat.get("cliffhanger_tag"),
                    "action_lines": _line_list(beat, "action_lines", "action"),
                    "dialogue_lines": _line_list(beat, "dialogue_lines", "dialogue"),
                },
            )
        )
    return payloads


def _dialogue_excerpt(beat: dict[str, Any]) -> str | None:
    parts: list[str] = []
    for line in _line_list(beat, "dialogue_lines", "dialogue")[:3]:
        if not isinstance(line, dict):
            continue
        who = line.get("character") or line.get("speaker") or "旁白"
        text = line.get("content") or line.get("line") or line.get("text") or ""
        if text:
            parts.append(f"{who}: {text}")
    return "\n".join(parts) or None


def _characters_involved(beat: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for line in _line_list(beat, "dialogue_lines", "dialogue"):
        if not isinstance(line, dict):
            continue
        name = line.get("character") or line.get("speaker")
        if name and name not in out:
            out.append(str(name))
    return out


def _line_list(beat: dict[str, Any], primary: str, fallback: str) -> list[Any]:
    raw = beat.get(primary)
    if isinstance(raw, list):
        return raw
    raw = beat.get(fallback)
    return raw if isinstance(raw, list) else []
