"""Video trimming helpers (ffmpeg).

Used to post-process provider videos so the final clip duration matches the
storyboard timeline (target seconds), even when the provider only supports
discrete durations.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

import httpx


async def download_video_bytes(url: str, *, timeout: float = 120.0) -> bytes:
    """Download a video URL into memory."""
    if not url:
        raise RuntimeError("video_download_url_empty")
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


def _run_ffmpeg(args: list[str]) -> None:
    completed = subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if completed.returncode != 0:
        raise RuntimeError(f"ffmpeg_failed: {completed.stderr[-2000:]}")


def trim_video_bytes(
    *,
    video_bytes: bytes,
    target_seconds: float,
    input_ext: str = ".mp4",
    output_ext: Optional[str] = None,
) -> bytes:
    """Trim a video to the given duration (seconds) and return the new bytes.

    Attempts stream copy first; falls back to re-encode if needed.
    """
    if not video_bytes:
        raise RuntimeError("video_bytes_empty")
    if target_seconds <= 0:
        raise RuntimeError("target_seconds_invalid")

    out_ext = output_ext or input_ext or ".mp4"
    with TemporaryDirectory(prefix="video_trim_") as tmpdir:
        tmp_path = Path(tmpdir)
        in_path = tmp_path / f"input{input_ext}"
        out_path = tmp_path / f"output{out_ext}"
        in_path.write_bytes(video_bytes)

        t_arg = f"{float(target_seconds):.3f}"

        # Fast path: stream copy.
        try:
            _run_ffmpeg(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(in_path),
                    "-t",
                    t_arg,
                    "-c",
                    "copy",
                    "-movflags",
                    "+faststart",
                    str(out_path),
                ]
            )
        except Exception:
            # Fallback: re-encode for robustness when copy trimming fails.
            _run_ffmpeg(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(in_path),
                    "-t",
                    t_arg,
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "23",
                    "-c:a",
                    "aac",
                    "-movflags",
                    "+faststart",
                    str(out_path),
                ]
            )

        if not out_path.exists() or out_path.stat().st_size <= 0:
            raise RuntimeError("video_trim_empty_output")
        return out_path.read_bytes()

