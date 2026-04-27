"""
Audio generation utilities.

Provides low-level audio processing functions including:
- WAV/MP3 file operations
- TTS audio generation
- Audio concatenation and encoding
"""

from __future__ import annotations

import subprocess
import wave
from pathlib import Path
from typing import Any, Sequence

import httpx
from app.core.logging import get_logger
from app.services.ai_service import ai_service
from app.services.audio.audio_emotions import (
    ALLOWED_TTS_EMOTIONS as ALLOWED_TTS_EMOTIONS,
)
from app.services.audio.audio_emotions import (
    normalize_tts_emotion as normalize_tts_emotion,
)

logger = get_logger(__name__)
_MISSING_OSS = object()


def ensure_oss_configured(oss_svc=_MISSING_OSS) -> None:
    """Ensure OSS service is configured.

    When called without arguments, imports the singleton from oss_service.
    """
    if oss_svc is _MISSING_OSS:
        from app.services.storage.oss_service import oss_service as _oss

        oss_svc = _oss
    if not oss_svc:
        raise RuntimeError("OSS service not configured, cannot persist audio")


def wav_duration_ms(path: Path) -> int:
    """Get WAV file duration in milliseconds."""
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        if not rate:
            return 0
        return int(round(frames * 1000 / rate))


def run_ffmpeg(args: list[str]) -> None:
    """Run ffmpeg command with error handling."""
    completed = subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if completed.returncode != 0:
        raise RuntimeError(f"ffmpeg_failed: {completed.stderr[-2000:]}")


def generate_silence_wav(
    path: Path,
    duration_ms: int,
    sample_rate: int = 24000,
) -> None:
    """Generate a silent WAV file of specified duration."""
    duration_s = max(0.0, float(duration_ms) / 1000.0)
    run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=channel_layout=mono:sample_rate={sample_rate}",
            "-t",
            f"{duration_s:.3f}",
            "-acodec",
            "pcm_s16le",
            str(path),
        ]
    )


def normalize_wav(
    in_path: Path,
    out_path: Path,
    *,
    sample_rate: int = 24000,
) -> None:
    """Normalize WAV to consistent format (mono PCM s16le) for ffmpeg concat."""
    run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(in_path),
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            str(out_path),
        ]
    )


async def download_to_file(url: str, path: Path) -> None:
    """Download file from URL to local path."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        path.write_bytes(resp.content)


async def tts_to_wav_file(
    *,
    text: str,
    voice_config: dict[str, Any],
    out_path: Path,
    emotion: str | None = None,
    tts_speed: float = 1.0,
    tts_format: str = "wav",
) -> None:
    """Generate TTS audio and save to WAV file."""
    if not ai_service.ai_manager:
        raise RuntimeError("AI manager not initialized, cannot perform TTS")

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

    await download_to_file(str(audio_url), out_path)


def concat_wavs(paths: Sequence[Path], out_wav: Path) -> None:
    """Concatenate multiple WAV files into one."""
    concat_file = out_wav.parent / "concat.txt"
    concat_file.write_text(
        "".join(f"file '{p.as_posix()}'\n" for p in paths),
        encoding="utf-8",
    )
    run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            "24000",
            str(out_wav),
        ]
    )


def encode_mp3(in_wav: Path, out_mp3: Path, bitrate: str = "128k") -> None:
    """Encode WAV file to MP3."""
    run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(in_wav),
            "-acodec",
            "libmp3lame",
            "-b:a",
            bitrate,
            str(out_mp3),
        ]
    )


def concat_mp3s(paths: Sequence[Path], out_mp3: Path) -> None:
    """Concatenate MP3s into one MP3.

    Workaround: Some ffmpeg builds may fail when re-encoding directly from the
    concat demuxer (``inadequate AVFrame plane padding``).  Decode to normalized
    WAV first, concat WAV, then encode once.
    """
    if not paths:
        raise RuntimeError("no_mp3s_to_concat")

    tmp_dir = out_mp3.parent
    wav_paths: list[Path] = []
    for idx, mp3 in enumerate(paths, start=1):
        wav = tmp_dir / f"concat-src-{idx}.wav"
        normalize_wav(mp3, wav)
        wav_paths.append(wav)

    merged_wav = tmp_dir / "concat-merged.wav"
    concat_wavs(wav_paths, merged_wav)
    encode_mp3(merged_wav, out_mp3)
