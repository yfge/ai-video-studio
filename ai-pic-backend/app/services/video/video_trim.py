"""Video trimming helpers (ffmpeg).

Used to post-process provider videos so the final clip duration matches the
storyboard timeline (target seconds), even when the provider only supports
discrete durations.
"""

from __future__ import annotations

import subprocess
from math import floor
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


def probe_video_duration_bytes(
    video_bytes: bytes,
    *,
    input_ext: str = ".mp4",
) -> float | None:
    if not video_bytes:
        return None
    with TemporaryDirectory(prefix="video_probe_") as tmpdir:
        path = Path(tmpdir) / f"input{input_ext}"
        path.write_bytes(video_bytes)
        completed = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if completed.returncode != 0:
            return None
        try:
            duration = float(completed.stdout.strip())
        except (TypeError, ValueError):
            return None
        return duration if duration > 0 else None


def video_exceeds_target_by_more_than_one_frame(
    actual_seconds: float,
    target_seconds: float,
    target_fps: float | None,
) -> bool:
    _, aligned_target = frame_aligned_duration(target_seconds, target_fps)
    frame_seconds = 1 / target_fps if target_fps and target_fps > 0 else 0.001
    return actual_seconds > aligned_target + frame_seconds + 0.001


def trim_video_bytes(
    *,
    video_bytes: bytes,
    target_seconds: float,
    target_fps: float | None = None,
    input_ext: str = ".mp4",
    output_ext: Optional[str] = None,
) -> bytes:
    """Trim a video to the given duration (seconds) and return the new bytes.

    Re-encodes so trimming is frame accurate. Stream copy can retain packets
    beyond the requested time when the cut is not on a keyframe.
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

        frame_count, aligned_seconds = frame_aligned_duration(
            float(target_seconds), target_fps
        )
        args = [
            "ffmpeg",
            "-y",
            "-i",
            str(in_path),
            "-t",
            f"{aligned_seconds:.6f}",
        ]
        if frame_count is not None:
            args.extend(["-frames:v", str(frame_count)])
        args.extend(
            [
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
        _run_ffmpeg(args)

        if not out_path.exists() or out_path.stat().st_size <= 0:
            raise RuntimeError("video_trim_empty_output")
        return out_path.read_bytes()


def extract_video_frame_bytes(
    *,
    video_bytes: bytes,
    frame_index: int,
    input_ext: str = ".mp4",
) -> bytes:
    """Decode one zero-based video frame as PNG bytes."""
    if not video_bytes:
        raise RuntimeError("video_bytes_empty")
    if frame_index < 0:
        raise RuntimeError("frame_index_invalid")
    with TemporaryDirectory(prefix="video_frame_") as tmpdir:
        tmp_path = Path(tmpdir)
        in_path = tmp_path / f"input{input_ext}"
        out_path = tmp_path / "frame.png"
        in_path.write_bytes(video_bytes)
        _run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(in_path),
                "-vf",
                f"select=eq(n\\,{frame_index})",
                "-frames:v",
                "1",
                str(out_path),
            ]
        )
        if not out_path.exists() or out_path.stat().st_size <= 0:
            raise RuntimeError("video_frame_empty_output")
        return out_path.read_bytes()


def frame_aligned_duration(
    target_seconds: float,
    target_fps: float | None,
) -> tuple[int | None, float]:
    if target_fps is None or target_fps <= 0:
        return None, target_seconds
    frame_count = max(1, floor(target_seconds * target_fps + 1e-9))
    return frame_count, frame_count / target_fps
