"""Scene audio validation and persistence helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.models.script import Script
from app.models.story_structure import Scene, SceneBeat
from app.repositories.audio_timeline_repository import list_active_scene_beats
from sqlalchemy.orm import Session

logger = get_logger(__name__)


def validate_duration(
    scene: Scene,
    scene_number: int,
    duration_ms: int,
    duration_seconds: float,
    target_duration_seconds: int | None,
) -> None:
    if not target_duration_seconds:
        return
    target_ms = target_duration_seconds * 1000
    ratio = duration_ms / target_ms if target_ms > 0 else 0
    logger.info(
        "Scene dialogue audio duration validation",
        extra={
            "scene_id": scene.id,
            "scene_number": scene_number,
            "target_duration_seconds": target_duration_seconds,
            "actual_duration_seconds": duration_seconds,
            "duration_ratio": round(ratio, 2),
            "within_tolerance": 0.7 <= ratio <= 1.3,
        },
    )
    if ratio < 0.7:
        logger.warning(
            f"Scene {scene_number} duration too short: "
            f"{duration_seconds}s vs target {target_duration_seconds}s ({ratio:.0%})"
        )
    elif ratio > 1.3:
        logger.warning(
            f"Scene {scene_number} duration too long: "
            f"{duration_seconds}s vs target {target_duration_seconds}s ({ratio:.0%})"
        )


def persist_beats(
    db: Session,
    beats: list[dict[str, Any]],
    scene: Scene,
    scene_character_names: list[str],
    overwrite_beats: bool,
) -> None:
    if overwrite_beats:
        for beat in list_active_scene_beats(db, scene.id):
            beat.soft_delete(reason="dialogue_audio_overwrite")

    start_ms = 0
    for idx, beat in enumerate(beats, start=1):
        dur_ms = int(beat.get("duration_ms") or 0)
        end_ms = start_ms + dur_ms
        db.add(
            SceneBeat(
                scene_id=scene.id,
                order_index=idx,
                beat_type=beat.get("beat_type"),
                beat_summary=beat.get("beat_summary"),
                characters_involved=scene_character_names or None,
                dialogue_excerpt=beat.get("dialogue_excerpt"),
                duration_seconds=round(dur_ms / 1000.0, 3),
                extra_metadata={
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "speaker_name": beat.get("speaker_name"),
                    "speaker_kind": beat.get("speaker_kind"),
                    "voice_config": beat.get("voice_config"),
                    "emotion": beat.get("emotion"),
                    "tts_emotion": beat.get("tts_emotion"),
                    "action": beat.get("action"),
                    "source": "dialogue_audio_pipeline",
                },
            )
        )
        start_ms = end_ms


def update_scene_metadata(
    db: Session,
    scene: Scene,
    script: Script,
    oss_result: dict,
    duration_seconds: float,
) -> dict[str, Any]:
    extra = dict(scene.extra_metadata or {})
    prev = extra.get("dialogue_audio")
    prev_version = 0
    if isinstance(prev, dict):
        try:
            prev_version = int(prev.get("version") or 0)
        except Exception:
            prev_version = 0
    payload = {
        "oss_url": oss_result["file_url"],
        "duration_seconds": duration_seconds,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "version": prev_version + 1,
        "script_id": script.id,
    }
    extra["dialogue_audio"] = payload
    scene.extra_metadata = extra
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return payload
