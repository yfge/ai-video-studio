"""Audio time-stretch helpers (ffmpeg atempo chain)."""

from __future__ import annotations

from pathlib import Path


def build_atempo_chain(speed: float) -> str:
    """Build a safe ffmpeg `atempo` filter chain for the given speed.

    ffmpeg `atempo` supports 0.5-2.0 per filter, so we chain multiple filters
    to cover a wider range.
    """
    try:
        speed_f = float(speed)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError("invalid_speed") from exc

    if speed_f <= 0:  # pragma: no cover - defensive
        raise ValueError("speed_must_be_positive")

    chain: list[str] = []
    # Speed up (shorten duration)
    while speed_f > 2.0:
        chain.append("atempo=2.0")
        speed_f /= 2.0
    # Slow down (lengthen duration)
    while speed_f < 0.5:
        chain.append("atempo=0.5")
        speed_f /= 0.5

    chain.append(f"atempo={speed_f:.6f}")
    return ",".join(chain)


def time_stretch_wav_ffmpeg_args(
    *,
    in_path: Path,
    out_path: Path,
    speed: float,
    sample_rate: int = 24000,
) -> list[str]:
    """Build an ffmpeg command to time-stretch a WAV to a normalized WAV."""
    chain = build_atempo_chain(speed)
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(in_path),
        "-filter:a",
        chain,
        "-acodec",
        "pcm_s16le",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        str(out_path),
    ]
