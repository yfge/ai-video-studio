"""Sync script scene payloads into normalized story structure tables."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.models.script import Script
from app.models.story_structure import Scene
from app.schemas.story_structure import SceneCreate, ShotCreate
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
        return {"created": 0, "shots_created": 0, "skipped": 0}

    existing = story_structure_svc.list_scenes_by_script(db, script.id)
    if existing and not allow_overwrite:
        return {"created": 0, "shots_created": 0, "skipped": len(existing)}

    if allow_overwrite and existing:
        for scene in existing:
            try:
                story_structure_svc.delete_scene(db, scene.id)
            except Exception as exc:  # pragma: no cover - protective
                logger.warning("failed to delete old normalized scene: %s", exc)

    scenes_src = script.scenes or []
    if not scenes_src and isinstance(script.extra_metadata, dict):
        scenes_src = script.extra_metadata.get("scenes") or []

    created_scenes: list[Scene] = []
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
            created_scenes.append(created)
        except Exception as exc:  # pragma: no cover - protective
            logger.warning("failed to write normalized scene %s: %s", scene_key, exc)

    shots_created = 0
    for scene in created_scenes:
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
        "created": len(created_scenes),
        "shots_created": shots_created,
        "skipped": len(existing) if existing and not allow_overwrite else 0,
    }
