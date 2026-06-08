"""Compatibility facade for historical dialogue audio imports.

Production scene-audio, episode-audio, beat, and storyboard logic now lives under
``app.services.audio``. This module remains as a thin import surface for older
callers and tests that still import the historical service path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.ai_service import ai_service
from app.services.audio.audio_emotions import (
    normalize_tts_emotion as _normalize_tts_emotion,
)
from app.services.audio.audio_generator import concat_mp3s as _concat_mp3s
from app.services.audio.audio_generator import concat_wavs as _concat_wavs
from app.services.audio.audio_generator import download_to_file as _download_to_file
from app.services.audio.audio_generator import encode_mp3 as _encode_mp3
from app.services.audio.audio_generator import (
    ensure_oss_configured as _ensure_oss_configured,
)
from app.services.audio.audio_generator import (
    generate_silence_wav as _generate_silence_wav,
)
from app.services.audio.audio_generator import normalize_wav as _normalize_wav
from app.services.audio.audio_generator import run_ffmpeg as _run_ffmpeg
from app.services.audio.audio_generator import wav_duration_ms as _wav_duration_ms
from app.services.audio.dialogue_processing.segment_models import PlannedSegment
from app.services.audio.dialogue_service_compat import plan_scene_segments
from app.services.audio.dialogue_service_text_compat import (
    looks_like_silence as _looks_like_silence,
)
from app.services.audio.dialogue_service_text_compat import norm_name as _norm_name
from app.services.audio.dialogue_service_text_compat import (
    sanitize_dialogue_content as _sanitize_dialogue_content,
)
from app.services.audio.episode_audio_builder import (  # noqa: F401
    generate_episode_audio_timeline,
)
from app.services.audio.episode_timeline_beats import (  # noqa: F401
    build_episode_timeline_beats,
)
from app.services.audio.scene_audio_generator import (  # noqa: F401
    generate_scene_dialogue_audio,
)
from app.services.audio.storyboard_from_timeline import (  # noqa: F401
    build_storyboard_frames_from_audio_timeline,
    generate_storyboard_from_episode_audio_timeline,
)

__all__ = [
    "PlannedSegment",
    "build_episode_timeline_beats",
    "build_storyboard_frames_from_audio_timeline",
    "generate_episode_audio_timeline",
    "generate_scene_dialogue_audio",
    "generate_storyboard_from_episode_audio_timeline",
    "plan_scene_segments",
    "_concat_mp3s",
    "_concat_wavs",
    "_download_to_file",
    "_encode_mp3",
    "_ensure_oss_configured",
    "_generate_silence_wav",
    "_looks_like_silence",
    "_norm_name",
    "_normalize_tts_emotion",
    "_normalize_wav",
    "_run_ffmpeg",
    "_sanitize_dialogue_content",
    "_tts_to_wav_file",
    "_wav_duration_ms",
]


async def _tts_to_wav_file(
    *,
    text: str,
    voice_config: dict[str, Any],
    out_path: Path,
    emotion: str | None = None,
    tts_speed: float = 1.0,
    tts_format: str = "wav",
) -> None:
    """Historical wrapper kept so tests can monkeypatch this module's downloader."""
    if not ai_service.ai_manager:
        raise RuntimeError("AI 管理器未初始化，无法进行 TTS")

    provider = (voice_config.get("provider") or "minimax").strip()
    model = (voice_config.get("tts_model") or "speech-2.6-hd").strip()
    voice_id = (voice_config.get("voice_id") or "").strip() or None
    voice_type = (voice_config.get("voice_type") or "").strip() or None

    kwargs: dict[str, Any] = {"format": tts_format}
    if voice_id:
        kwargs["voice_id"] = voice_id
    if voice_type:
        kwargs["voice_type"] = voice_type
    if emotion:
        kwargs["emotion"] = emotion

    resp = await ai_service.ai_manager.text_to_speech(
        text=text,
        model=model,
        prefer_provider=provider,
        speed=tts_speed,
        **kwargs,
    )
    if not resp.success:
        raise RuntimeError(resp.error or "TTS failed")
    audio_url = None
    if isinstance(resp.data, dict):
        audio_url = resp.data.get("audio_url")
    if not audio_url:
        raise RuntimeError("TTS did not return audio_url")

    await _download_to_file(str(audio_url), out_path)
