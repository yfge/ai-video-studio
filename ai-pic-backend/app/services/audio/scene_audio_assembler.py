"""Scene audio assembly and persistence.

Assembles TTS segments into a scene audio track, uploads to OSS,
and persists beats into the database.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene
from app.services.audio.audio_generator import (
    concat_wavs,
    encode_mp3,
    generate_silence_wav,
    wav_duration_ms,
)
from app.services.audio.scene_audio_persistence import (
    persist_beats,
    update_scene_metadata,
    validate_duration,
)
from app.services.audio.scene_fallback_tts import fallback_tts
from app.services.storage.oss_service import oss_service
from sqlalchemy.orm import Session


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


async def assemble_scene_audio(
    db: Session,
    *,
    segments: list,
    dialogue_tts_results: list[dict[str, Any]],
    tmp_root_path: Path,
    scene: Scene,
    episode: Episode,
    script: Script,
    story: Story,
    story_char_map: dict,
    scene_number: int,
    scene_character_names: list[str],
    tts_model: str,
    overwrite_beats: bool,
    target_duration_seconds: int | None,
) -> dict[str, Any]:
    """Assemble audio segments, upload to OSS, and persist beats."""
    wav_paths: list[Path] = []
    beats: list[dict[str, Any]] = []
    tts_lookup = {res["content"]: res for res in dialogue_tts_results}

    for seg in segments:
        if seg.kind == "pause":
            planned_ms = (
                int(seg.planned_duration_ms)
                if seg.planned_duration_ms is not None
                else 300
            )
            silence_wav = tmp_root_path / f"pause-{len(wav_paths)+1}.wav"
            generate_silence_wav(silence_wav, planned_ms)
            dur_ms = wav_duration_ms(silence_wav)
            wav_paths.append(silence_wav)
            beats.append(
                {
                    "beat_type": "pause",
                    "dialogue_excerpt": None,
                    "beat_summary": None,
                    "speaker_name": None,
                    "speaker_kind": None,
                    "voice_config": None,
                    "duration_ms": dur_ms,
                }
            )
            continue

        if seg.kind == "action":
            planned_ms = (
                int(seg.planned_duration_ms)
                if seg.planned_duration_ms is not None
                else 800
            )
            action_wav = tmp_root_path / f"action-{len(wav_paths)+1}.wav"
            generate_silence_wav(action_wav, planned_ms)
            dur_ms = wav_duration_ms(action_wav)
            wav_paths.append(action_wav)
            beats.append(
                {
                    "beat_type": "action",
                    "dialogue_excerpt": None,
                    "beat_summary": seg.text,
                    "speaker_name": None,
                    "speaker_kind": None,
                    "voice_config": None,
                    "duration_ms": dur_ms,
                }
            )
            continue

        # Dialogue segment - reuse pre-generated TTS from Phase 1
        tts_result = tts_lookup.get(seg.text)
        if tts_result:
            wav_paths.append(tts_result["wav_path"])
            beats.append(
                {
                    "beat_type": "dialogue",
                    "dialogue_excerpt": seg.text,
                    "beat_summary": None,
                    "speaker_name": tts_result["speaker"],
                    "speaker_kind": tts_result["speaker_kind"],
                    "voice_config": tts_result["voice_config"],
                    "emotion": tts_result["emotion"],
                    "tts_emotion": tts_result["tts_emotion"],
                    "action": tts_result["action"],
                    "duration_ms": tts_result["actual_duration_ms"],
                }
            )
        else:
            beat = await fallback_tts(
                db,
                seg,
                story_char_map,
                story,
                episode,
                scene,
                script,
                tts_model,
                tmp_root_path,
                len(wav_paths) + 1,
            )
            wav_paths.append(beat.pop("_wav_path"))
            beats.append(beat)

    scene_wav = tmp_root_path / "scene.wav"
    concat_wavs(wav_paths, scene_wav)
    scene_mp3 = tmp_root_path / "scene.mp3"
    encode_mp3(scene_wav, scene_mp3)

    duration_ms_total = wav_duration_ms(scene_wav)
    duration_seconds_total = round(duration_ms_total / 1000.0, 3)

    validate_duration(
        scene,
        scene_number,
        duration_ms_total,
        duration_seconds_total,
        target_duration_seconds,
    )

    oss_result = await oss_service.upload_file_content(
        file_content=scene_mp3.read_bytes(),
        filename=f"episode{episode.id}-scene{scene_number}.mp3",
        file_type="audio",
        prefix="episode-dialogue/scenes",
        metadata={
            "episode_id": episode.id,
            "scene_id": scene.id,
            "scene_number": scene_number,
            "duration_seconds": duration_seconds_total,
            "generated_at": _utc_now_iso(),
        },
    )
    if not oss_result.get("success") or not oss_result.get("file_url"):
        raise RuntimeError(f"OSS 上传失败: {oss_result}")

    persist_beats(db, beats, scene, scene_character_names, overwrite_beats)
    return update_scene_metadata(
        db,
        scene,
        script,
        oss_result,
        duration_seconds_total,
    )
