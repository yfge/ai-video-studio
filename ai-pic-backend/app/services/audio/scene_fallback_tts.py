"""Fallback TTS generation for scene audio assembly."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene
from app.services.audio.audio_generator import (
    normalize_tts_emotion,
    normalize_wav,
    tts_to_wav_file,
    wav_duration_ms,
)
from app.services.audio.dialogue_processing.text_utils import norm_name
from app.services.voice_binding_service import (
    ensure_derived_character_voice_binding,
    ensure_virtual_ip_voice_config,
)
from sqlalchemy.orm import Session

logger = get_logger(__name__)


async def fallback_tts(
    db: Session,
    seg,
    story_char_map: dict,
    story: Story,
    episode: Episode,
    scene: Scene,
    script: Script,
    tts_model: str,
    tmp_root_path: Path,
    idx: int,
) -> dict[str, Any]:
    """Generate TTS on-the-fly for a segment not found in Phase 1 cache."""
    logger.warning(
        "Dialogue not found in Phase 1 TTS cache, generating on-the-fly",
        extra={
            "scene_id": scene.id,
            "text_preview": seg.text[:50] if seg.text else None,
        },
    )
    speaker = seg.speaker_name or "旁白"
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

    raw = tmp_root_path / f"fallback-dlg-{idx}-raw.wav"
    local = tmp_root_path / f"fallback-dlg-{idx}.wav"
    tts_emotion = normalize_tts_emotion(seg.emotion, action=seg.action)
    await tts_to_wav_file(
        text=seg.text,
        voice_config=voice_config,
        out_path=raw,
        emotion=tts_emotion,
    )
    normalize_wav(raw, local)
    return {
        "_wav_path": local,
        "beat_type": "dialogue",
        "dialogue_excerpt": seg.text,
        "beat_summary": None,
        "speaker_name": speaker,
        "speaker_kind": speaker_kind,
        "voice_config": voice_config,
        "emotion": seg.emotion,
        "tts_emotion": tts_emotion,
        "action": seg.action,
        "duration_ms": wav_duration_ms(local),
    }


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
