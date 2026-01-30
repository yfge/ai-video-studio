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

logger = get_logger(__name__)


# Allowed TTS emotion labels
ALLOWED_TTS_EMOTIONS = {
    "happy",
    "sad",
    "angry",
    "fearful",
    "disgusted",
    "surprised",
    "calm",
    "fluent",
    "whisper",
}


def ensure_oss_configured(oss_service) -> None:
    """Ensure OSS service is configured."""
    if not oss_service:
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


def normalize_tts_emotion(
    emotion: str | None,
    *,
    action: str | None = None,
) -> str | None:
    """Normalize emotion string to allowed TTS emotion labels."""
    if not emotion and not action:
        return None

    raw = " ".join(
        v.strip()
        for v in [emotion or "", action or ""]
        if isinstance(v, str) and v.strip()
    )
    if not raw:
        return None

    raw_lower = raw.lower()

    # Direct match
    if isinstance(emotion, str) and emotion.strip().lower() in ALLOWED_TTS_EMOTIONS:
        return emotion.strip().lower()

    def _has_any(tokens: Sequence[str]) -> bool:
        return any(tok in raw_lower for tok in tokens)

    # Emotion detection rules
    if _has_any(
        ["whisper", "低语", "耳语", "压低", "小声", "悄声", "轻声", "低声", "自语"]
    ):
        return "whisper"
    if _has_any(["angry", "愤怒", "生气", "恼火", "怒", "火大", "暴躁"]):
        return "angry"
    if _has_any(
        [
            "sad",
            "悲伤",
            "难过",
            "沮丧",
            "哽咽",
            "哭",
            "伤心",
            "叹气",
            "叹了口气",
            "叹了一口气",
            "叹息",
            "长叹",
        ]
    ):
        return "sad"
    if _has_any(["happy", "高兴", "开心", "喜悦", "兴奋", "激动", "欢快", "愉快"]):
        return "happy"
    if _has_any(["surprised", "惊讶", "吃惊", "震惊", "惊"]):
        return "surprised"
    if _has_any(["fearful", "害怕", "恐惧", "紧张", "慌", "担心", "焦虑", "畏惧"]):
        return "fearful"
    if _has_any(["disgusted", "厌恶", "恶心", "反感"]):
        return "disgusted"
    if _has_any(
        [
            "calm",
            "neutral",
            "thoughtful",
            "平静",
            "冷静",
            "中性",
            "沉稳",
            "严肃",
            "思考",
            "克制",
        ]
    ):
        return "calm"
    if _has_any(
        [
            "fluent",
            "confident",
            "assertive",
            "自信",
            "坚定",
            "果断",
            "专业",
            "流利",
            "从容",
        ]
    ):
        return "fluent"

    # Safety fallback
    return None


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
    """Concatenate multiple MP3 files into one."""
    concat_file = out_mp3.parent / "concat.txt"
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
            "copy",
            str(out_mp3),
        ]
    )
