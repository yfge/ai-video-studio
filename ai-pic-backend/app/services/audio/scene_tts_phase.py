"""TTS generation phase for scene dialogue audio."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene
from app.services.audio.audio_generator import (
    normalize_tts_emotion,
    normalize_wav,
    run_ffmpeg,
    tts_to_wav_file,
    wav_duration_ms,
)
from app.services.audio.dialogue_processing.text_utils import norm_name
from app.services.audio.time_stretch import time_stretch_wav_ffmpeg_args
from app.services.voice_binding_service import (
    ensure_derived_character_voice_binding,
    ensure_virtual_ip_voice_config,
)
from sqlalchemy.orm import Session

logger = get_logger(__name__)


async def generate_dialogue_tts_phase(
    db: Session,
    dialogues: list[dict[str, Any]],
    story_char_map: dict,
    story: Story,
    episode: Episode,
    scene: Scene,
    script: Script,
    tts_model: str,
    tmp_root_path: Path,
) -> tuple[list[dict[str, Any]], int]:
    """Generate TTS for all dialogues and return actual durations."""
    results: list[dict[str, Any]] = []
    total_ms = 0

    for idx, dlg in enumerate(dialogues):
        content = dlg.get("content") or ""
        if not content.strip():
            continue

        speaker = dlg.get("character") or "旁白"
        voice_config, speaker_kind = await _voice_config(
            db,
            story_char_map,
            story,
            episode,
            scene,
            script,
            speaker,
            tts_model,
        )

        raw_path = tmp_root_path / f"phase1-dlg-{idx}-raw.wav"
        wav_path = tmp_root_path / f"phase1-dlg-{idx}.wav"
        emotion, action = dlg.get("emotion"), dlg.get("action")
        tts_emotion = normalize_tts_emotion(emotion, action=action)
        await tts_to_wav_file(
            text=content,
            voice_config=voice_config,
            out_path=raw_path,
            emotion=tts_emotion,
        )
        normalize_wav(raw_path, wav_path)
        actual_ms = wav_duration_ms(wav_path)
        total_ms += actual_ms

        results.append(
            {
                "index": idx,
                "speaker": speaker,
                "speaker_kind": speaker_kind,
                "content": content,
                "emotion": emotion,
                "action": action,
                "tts_emotion": tts_emotion,
                "voice_config": voice_config,
                "wav_path": wav_path,
                "actual_duration_ms": actual_ms,
            }
        )

    return results, total_ms


def compress_dialogue_tts_to_target(
    tts_results: list[dict[str, Any]],
    total_ms: int,
    target_duration_seconds: int,
    scene: Scene,
    scene_number: int,
    tmp_root_path: Path,
) -> int:
    """Compress dialogues via time-stretch if they exceed the target budget."""
    target_ms = int(target_duration_seconds * 1000)
    allowed_ms = max(1000, target_ms - 1000)
    if total_ms <= allowed_ms:
        return total_ms

    speed = total_ms / allowed_ms
    logger.warning(
        "Dialogues exceed scene target; time-stretching dialogues",
        extra={
            "scene_id": scene.id,
            "scene_number": scene_number,
            "target_duration_seconds": target_duration_seconds,
            "target_ms": target_ms,
            "dialogue_ms_before": total_ms,
            "dialogue_ms_allowed": allowed_ms,
            "speed_factor": round(speed, 3),
        },
    )
    new_total = 0
    for res in tts_results:
        stretched = tmp_root_path / f"phase1-dlg-{res['index']}-stretched.wav"
        run_ffmpeg(
            time_stretch_wav_ffmpeg_args(
                in_path=res["wav_path"],
                out_path=stretched,
                speed=speed,
            )
        )
        new_ms = wav_duration_ms(stretched)
        res["wav_path"] = stretched
        res["actual_duration_ms"] = new_ms
        res["audio_speed"] = round(speed, 6)
        new_total += new_ms
    return new_total


async def _voice_config(
    db: Session,
    story_char_map: dict,
    story: Story,
    episode: Episode,
    scene: Scene,
    script: Script,
    speaker: str,
    tts_model: str,
) -> tuple[dict[str, Any], str]:
    ip = story_char_map.get(norm_name(speaker))
    if ip:
        voice_config = await ensure_virtual_ip_voice_config(
            db, ip, tts_provider="minimax", tts_model=tts_model
        )
        return voice_config, "virtual_ip"

    _, voice_config = await ensure_derived_character_voice_binding(
        db,
        story=story,
        episode=episode,
        scene=scene,
        script_dialogues=script.dialogues or [],
        character_name=speaker,
        tts_provider="minimax",
        tts_model=tts_model,
    )
    return voice_config, "derived"
