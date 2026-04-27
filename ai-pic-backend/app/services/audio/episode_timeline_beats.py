"""Episode audio timeline beat construction."""

from __future__ import annotations

from typing import Any, Sequence

from app.models.story_structure import Scene, SceneBeat


def build_episode_timeline_beats(
    *,
    scenes: Sequence[Scene],
    beats_by_scene_id: dict[int, Sequence[SceneBeat]],
) -> tuple[list[dict[str, Any]], int]:
    """Build episode timeline from scenes and their beats."""
    offset_ms = 0
    merged: list[dict[str, Any]] = []

    for scene in scenes:
        scene_id = int(scene.id)
        try:
            scene_number = int(str(scene.scene_number).strip())
        except Exception:
            scene_number = None

        cursor_ms = 0
        for beat in beats_by_scene_id.get(scene_id, []):
            meta = beat.extra_metadata if isinstance(beat.extra_metadata, dict) else {}
            start_ms_int = _parse_optional_ms(meta.get("start_ms"))
            end_ms_int = _parse_optional_ms(meta.get("end_ms"))

            if start_ms_int is None:
                start_ms_int = cursor_ms
            if end_ms_int is None:
                dur_s = float(beat.duration_seconds or 0)
                end_ms_int = start_ms_int + max(0, int(round(dur_s * 1000)))
            if end_ms_int < start_ms_int:
                end_ms_int = start_ms_int

            cursor_ms = end_ms_int
            merged.append(
                _timeline_beat(
                    scene_id,
                    scene_number,
                    beat,
                    meta,
                    offset_ms,
                    start_ms_int,
                    end_ms_int,
                )
            )

        offset_ms += cursor_ms

    return merged, offset_ms


def _parse_optional_ms(value: Any) -> int | None:
    if isinstance(value, (int, float, str)) and str(value).strip():
        return int(value)
    return None


def _timeline_beat(
    scene_id: int,
    scene_number: int | None,
    beat: SceneBeat,
    meta: dict[str, Any],
    offset_ms: int,
    start_ms: int,
    end_ms: int,
) -> dict[str, Any]:
    text = beat.dialogue_excerpt if beat.beat_type == "dialogue" else beat.beat_summary
    characters = _characters_involved(beat)
    return {
        "scene_id": scene_id,
        "scene_number": scene_number,
        "beat_id": int(beat.id),
        "beat_type": beat.beat_type,
        "speaker_name": meta.get("speaker_name"),
        "characters_involved": characters,
        "dialogue_action": meta.get("action") if beat.beat_type == "dialogue" else None,
        "dialogue_emotion": (
            meta.get("emotion") if beat.beat_type == "dialogue" else None
        ),
        "text": text,
        "start_ms": offset_ms + start_ms,
        "end_ms": offset_ms + end_ms,
    }


def _characters_involved(beat: SceneBeat) -> list[str] | None:
    characters = beat.characters_involved
    if not isinstance(characters, list):
        return None
    normalized = [str(item).strip() for item in characters if str(item).strip()]
    return normalized or None
