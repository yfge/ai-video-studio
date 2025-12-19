"""
Timeline and storyboard processing.

Provides functions for building audio timelines and generating
storyboard frames from audio timeline data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.script import Episode, Script
from app.models.story_structure import Scene, SceneBeat
from app.services.storyboard.storyboard_prompt_utils import (
    apply_storyboard_prompt_optimizations,
)


def utc_now_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


def build_episode_timeline_beats(
    *,
    scenes: Sequence[Scene],
    beats_by_scene_id: dict[int, Sequence[SceneBeat]],
) -> tuple[list[dict[str, Any]], int]:
    """
    Build episode timeline from scenes and their beats.

    Returns:
        Tuple of (merged timeline beats, total duration in ms)
    """
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

            start_ms = meta.get("start_ms")
            end_ms = meta.get("end_ms")

            start_ms_int = (
                int(start_ms)
                if isinstance(start_ms, (int, float, str)) and str(start_ms).strip()
                else None
            )
            end_ms_int = (
                int(end_ms)
                if isinstance(end_ms, (int, float, str)) and str(end_ms).strip()
                else None
            )

            if start_ms_int is None:
                start_ms_int = cursor_ms
            if end_ms_int is None:
                dur_s = float(beat.duration_seconds or 0)
                end_ms_int = start_ms_int + max(0, int(round(dur_s * 1000)))
            if end_ms_int < start_ms_int:
                end_ms_int = start_ms_int

            cursor_ms = end_ms_int

            text = (
                beat.dialogue_excerpt
                if beat.beat_type == "dialogue"
                else beat.beat_summary
            )
            merged.append({
                "scene_id": scene_id,
                "scene_number": scene_number,
                "beat_id": int(beat.id),
                "beat_type": beat.beat_type,
                "speaker_name": meta.get("speaker_name"),
                "text": text,
                "start_ms": offset_ms + start_ms_int,
                "end_ms": offset_ms + end_ms_int,
            })

        offset_ms += cursor_ms

    return merged, offset_ms


def build_storyboard_frames_from_audio_timeline(
    *,
    audio_timeline: dict[str, Any],
    min_pause_duration_ms: int = 1500,
) -> list[dict[str, Any]]:
    """
    Build storyboard frames from audio timeline beats.

    Args:
        audio_timeline: Audio timeline dictionary with beats.
        min_pause_duration_ms: Minimum pause duration to create separate frame.

    Returns:
        List of storyboard frame dictionaries.
    """
    beats = audio_timeline.get("beats") if isinstance(audio_timeline, dict) else None
    if not isinstance(beats, list):
        raise RuntimeError("audio_timeline_missing_beats")

    frames: list[dict[str, Any]] = []
    scene_index_map: dict[int, int] = {}
    next_scene_index = 1

    for beat in beats:
        if not isinstance(beat, dict):
            continue
        beat_type = beat.get("beat_type")
        if beat_type not in {"dialogue", "action", "pause"}:
            continue

        start_ms = beat.get("start_ms")
        end_ms = beat.get("end_ms")
        if start_ms is None or end_ms is None:
            continue
        try:
            start_ms_int = int(start_ms)
            end_ms_int = int(end_ms)
        except Exception:
            continue
        if end_ms_int < start_ms_int:
            continue

        scene_id = beat.get("scene_id")
        scene_id_int = (
            int(scene_id)
            if isinstance(scene_id, (int, str)) and str(scene_id).strip()
            else None
        )
        scene_number = beat.get("scene_number")
        try:
            scene_number_int = int(scene_number) if scene_number is not None else None
        except Exception:
            scene_number_int = None

        if scene_id_int is not None and scene_id_int not in scene_index_map:
            scene_index_map[scene_id_int] = next_scene_index
            next_scene_index += 1

        duration_ms = end_ms_int - start_ms_int

        # Handle short pauses by merging into previous frame
        if beat_type == "pause" and duration_ms < min_pause_duration_ms:
            if frames:
                last = frames[-1]
                last_end = last.get("end_ms")
                last_scene_number = last.get("scene_number")
                if (
                    isinstance(last_end, int)
                    and last_end == start_ms_int
                    and (
                        scene_number_int is None
                        or last_scene_number is None
                        or int(last_scene_number) == scene_number_int
                    )
                ):
                    last["end_ms"] = end_ms_int
                    last_start = last.get("start_ms")
                    if isinstance(last_start, int):
                        last["duration_seconds"] = round(
                            (end_ms_int - last_start) / 1000.0, 3
                        )
                    else:
                        last["duration_seconds"] = round(
                            float(last.get("duration_seconds") or 0.0)
                            + duration_ms / 1000.0,
                            3,
                        )
                    continue

            # No prior frame to merge; emit a short pause frame
            frames.append(_create_frame(
                scene_number_int=scene_number_int,
                scene_id_int=scene_id_int,
                scene_index_map=scene_index_map,
                description="（停顿）",
                duration_ms=duration_ms,
                start_ms_int=start_ms_int,
                end_ms_int=end_ms_int,
                frame_number=len(frames) + 1,
            ))
            continue

        # Create frame for dialogue, action, or long pause
        speaker = (
            (beat.get("speaker_name") or "旁白") if beat_type == "dialogue" else None
        )
        text = (beat.get("text") or "").strip()
        if beat_type == "dialogue":
            description = f"{speaker}: {text}".strip() if text else str(speaker)
        elif beat_type == "pause":
            description = "（停顿）"
        else:
            description = text or "（动作）"

        frames.append(_create_frame(
            scene_number_int=scene_number_int,
            scene_id_int=scene_id_int,
            scene_index_map=scene_index_map,
            description=description,
            duration_ms=duration_ms,
            start_ms_int=start_ms_int,
            end_ms_int=end_ms_int,
            frame_number=len(frames) + 1,
        ))

    return frames


def _create_frame(
    *,
    scene_number_int: int | None,
    scene_id_int: int | None,
    scene_index_map: dict[int, int],
    description: str,
    duration_ms: int,
    start_ms_int: int,
    end_ms_int: int,
    frame_number: int,
) -> dict[str, Any]:
    """Create a storyboard frame dictionary."""
    return {
        "frame_id": str(uuid4()),
        "frame_number": frame_number,
        "scene_number": scene_number_int,
        "scene_index": (
            scene_index_map.get(scene_id_int) if scene_id_int is not None else None
        ),
        "description": description,
        "duration_seconds": round(duration_ms / 1000.0, 3),
        "generation_source": "audio_timeline",
        "generation_method": "audio_timeline",
        "status": "draft",
        "start_ms": start_ms_int,
        "end_ms": end_ms_int,
    }


def generate_storyboard_from_episode_audio_timeline(
    db: Session,
    *,
    script: Script,
    episode: Episode,
    overwrite_existing: bool = False,
    min_pause_duration_ms: int = 1500,
) -> dict[str, Any]:
    """
    Generate storyboard frames from episode audio timeline.

    Persists storyboard into script.extra_metadata.

    Args:
        db: Database session.
        script: Script to update.
        episode: Episode with audio timeline.
        overwrite_existing: Whether to overwrite existing storyboard.
        min_pause_duration_ms: Minimum pause duration for separate frames.

    Returns:
        Dictionary with frames and metadata.
    """
    ep_meta = episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
    audio_timeline = (
        ep_meta.get("audio_timeline") if isinstance(ep_meta, dict) else None
    )
    if not isinstance(audio_timeline, dict):
        raise RuntimeError("episode_audio_timeline_not_found")
    if audio_timeline.get("script_id") != script.id:
        raise RuntimeError("audio_timeline_script_mismatch")

    frames = build_storyboard_frames_from_audio_timeline(
        audio_timeline=audio_timeline,
        min_pause_duration_ms=min_pause_duration_ms,
    )
    apply_storyboard_prompt_optimizations(frames)
    if not frames:
        raise RuntimeError("no_frames_generated_from_audio_timeline")

    # Check for existing assets if not overwriting
    extra = dict(script.extra_metadata or {})
    existing = extra.get("storyboard") if isinstance(extra, dict) else None
    if not overwrite_existing and isinstance(existing, dict):
        existing_frames = existing.get("frames")
        if isinstance(existing_frames, list):
            for frame in existing_frames:
                if not isinstance(frame, dict):
                    continue
                if any(
                    frame.get(key)
                    for key in (
                        "image_url",
                        "start_image_url",
                        "start_image_urls",
                        "end_image_url",
                        "end_image_urls",
                        "video_url",
                        "video_urls",
                    )
                ):
                    raise RuntimeError(
                        "storyboard_has_assets_refuse_overwrite: set overwrite_existing=true"
                    )

    sb_meta = {
        "generated_at": utc_now_iso(),
        "generation_source": "audio_timeline",
        "generation_method": "audio_timeline",
        "script_id": script.id,
        "episode_id": episode.id,
        "audio_timeline_version": (audio_timeline.get("episode_audio") or {}).get(
            "version"
        ),
    }
    extra["storyboard"] = {"frames": frames, "meta": sb_meta}
    script.extra_metadata = extra
    script.storyboard_updated_at = datetime.utcnow()
    script.storyboard_version = (script.storyboard_version or 0) + 1
    db.add(script)
    db.commit()
    db.refresh(script)

    return {"frames": frames, "meta": sb_meta}
