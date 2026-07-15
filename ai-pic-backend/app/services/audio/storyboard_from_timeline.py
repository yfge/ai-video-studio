"""Storyboard frame generation from audio timeline.

Builds rich storyboard frames from episode audio timeline beats,
with visual prompt descriptions and story context enrichment.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.models.script import Episode, Script
from app.services.audio.storyboard_timeline_helpers import (
    check_existing_assets,
    extract_characters,
    make_frame,
    parse_ms_range,
    parse_scene_ids,
    try_merge_pause,
)
from app.services.storyboard.storyboard_prompt_utils import (
    apply_storyboard_prompt_optimizations,
)
from sqlalchemy.orm import Session

logger = get_logger(__name__)


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def build_storyboard_frames_from_audio_timeline(
    *,
    audio_timeline: dict[str, Any],
    min_pause_duration_ms: int = 1500,
) -> list[dict[str, Any]]:
    """Build rich storyboard frames from audio timeline beats.

    This is the only implementation of audio-timeline support-view frames and
    includes ``characters``, ``prompt_description``, and ``scene_id`` per frame.
    """
    from app.services.storyboard.storyboard_audio_prompt_builder import (
        build_visual_prompt_description,
    )

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

        characters_involved = extract_characters(beat)
        start_ms, end_ms = parse_ms_range(beat)
        if start_ms is None or end_ms is None:
            continue

        scene_id_int, scene_number_int = parse_scene_ids(beat)
        if scene_id_int is not None and scene_id_int not in scene_index_map:
            scene_index_map[scene_id_int] = next_scene_index
            next_scene_index += 1

        duration_ms = end_ms - start_ms

        # Merge short pauses into previous frame
        if beat_type == "pause" and duration_ms < min_pause_duration_ms:
            if try_merge_pause(frames, start_ms, end_ms, duration_ms, scene_number_int):
                continue
            frames.append(
                _annotate_frame_source(
                    make_frame(
                        scene_id_int=scene_id_int,
                        scene_number_int=scene_number_int,
                        scene_index_map=scene_index_map,
                        beat_type="pause",
                        speaker=None,
                        text=None,
                        dialogue_action=None,
                        characters=characters_involved,
                        description="（停顿）",
                        duration_ms=duration_ms,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        frame_number=len(frames) + 1,
                        build_prompt=build_visual_prompt_description,
                    ),
                    beat,
                )
            )
            continue

        speaker = (
            (beat.get("speaker_name") or "旁白") if beat_type == "dialogue" else None
        )
        dialogue_action = (
            beat.get("dialogue_action") if beat_type == "dialogue" else None
        )
        text = (beat.get("text") or "").strip()
        if beat_type == "dialogue" and speaker:
            if speaker not in characters_involved:
                characters_involved.insert(0, speaker)
        if beat_type == "dialogue":
            description = f"{speaker}: {text}".strip() if text else str(speaker)
        elif beat_type == "pause":
            description = "（停顿）"
        else:
            description = text or "（动作）"

        frames.append(
            _annotate_frame_source(
                make_frame(
                    scene_id_int=scene_id_int,
                    scene_number_int=scene_number_int,
                    scene_index_map=scene_index_map,
                    beat_type=beat_type,
                    speaker=speaker,
                    text=text,
                    dialogue_action=dialogue_action,
                    characters=characters_involved,
                    description=description,
                    duration_ms=duration_ms,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    frame_number=len(frames) + 1,
                    build_prompt=build_visual_prompt_description,
                ),
                beat,
            )
        )

    return frames


def generate_storyboard_from_episode_audio_timeline(
    db: Session,
    *,
    script: Script,
    episode: Episode,
    overwrite_existing: bool = False,
    min_pause_duration_ms: int = 1500,
    legacy_support_view: bool = False,
) -> dict[str, Any]:
    """Generate storyboard frames from episode audio timeline and persist."""
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
    from app.services.storyboard.storyboard_audio_context_enricher import (
        enrich_storyboard_frames_with_story_context,
    )

    enrich_storyboard_frames_with_story_context(
        db,
        story_id=episode.story_id,
        script_id=script.id,
        frames=frames,
        max_reference_images=3,
        max_character_cards=3,
    )
    apply_storyboard_prompt_optimizations(frames)
    if not frames:
        raise RuntimeError("no_frames_generated_from_audio_timeline")

    extra = dict(script.extra_metadata or {})
    existing = extra.get("storyboard") if isinstance(extra, dict) else None
    if not overwrite_existing and isinstance(existing, dict):
        check_existing_assets(existing)

    sb_meta = {
        "generated_at": _utc_now_iso(),
        "generation_source": "audio_timeline",
        "generation_method": "audio_timeline",
        "source_role": (
            "legacy_audio_timeline_support_view"
            if legacy_support_view
            else "storyboard_support_view"
        ),
        "script_id": script.id,
        "episode_id": episode.id,
        "audio_timeline_version": (
            (audio_timeline.get("episode_audio") or {}).get("version")
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


def _annotate_frame_source(
    frame: dict[str, Any], beat: dict[str, Any]
) -> dict[str, Any]:
    generation_source = beat.get("generation_source")
    generation_method = beat.get("generation_method")
    if generation_source:
        frame["generation_source"] = generation_source
    if generation_method:
        frame["generation_method"] = generation_method
    for key in (
        "timeline_clip_id",
        "timeline_track_type",
        "timeline_id",
        "timeline_version",
        "source_audio_timeline_version",
    ):
        if beat.get(key) is not None:
            frame[key] = beat.get(key)
    source = beat.get("source")
    if isinstance(source, dict):
        frame["source"] = source
    return frame
