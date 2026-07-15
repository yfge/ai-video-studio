"""Normalize Timeline render clips to one deterministic video contract."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Sequence

from app.core.logging import get_logger
from app.services.render.video_ffmpeg import trim_clip_to_duration
from app.services.render.video_render_spec import RenderVideoSpec, allocate_frame_counts

logger = get_logger()


def prepare_render_clips(
    raw_paths: Sequence[str],
    durations: Sequence[float],
    descriptions: Sequence[str | None],
    work_dir: str,
    render_spec: RenderVideoSpec | None,
) -> tuple[list[str], str | None]:
    frame_counts = allocate_frame_counts(durations, render_spec) if render_spec else []
    paths: list[str] = []
    for index, raw_path in enumerate(raw_paths):
        output_path = os.path.join(work_dir, f"trimmed_{index:03d}.mp4")
        success = (
            normalize_video_clip(
                raw_path, output_path, spec=render_spec, frame_count=frame_counts[index]
            )
            if render_spec
            else trim_clip_to_duration(raw_path, output_path, durations[index])
        )
        if not success:
            return [], f"Clip normalization failed: {descriptions[index] or index}"
        paths.append(output_path)
    return paths, None


def normalize_video_clip(
    input_path: str,
    output_path: str,
    *,
    spec: RenderVideoSpec,
    frame_count: int,
) -> bool:
    """Re-encode one clip to the shared canvas, fps, codec, and frame count."""
    duration = frame_count / spec.fps
    filters = (
        f"[0:v]fps={spec.fps},split=2[bg][fg];"
        f"[bg]scale={spec.width}:{spec.height}:"
        "force_original_aspect_ratio=increase,"
        f"crop={spec.width}:{spec.height},boxblur=20:2[bgfill];"
        f"[fg]scale={spec.width}:{spec.height}:"
        "force_original_aspect_ratio=decrease[fgfit];"
        "[bgfill][fgfit]overlay=(W-w)/2:(H-h)/2,"
        f"tpad=stop_mode=clone:stop_duration={duration:.6f},"
        f"trim=end_frame={frame_count},setpts=PTS-STARTPTS,"
        "setsar=1,format=yuv420p[outv]"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-filter_complex",
        filters,
        "-map",
        "[outv]",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "20",
        "-r",
        str(spec.fps),
        "-frames:v",
        str(frame_count),
        "-movflags",
        "+faststart",
        output_path,
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=600, check=True)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        logger.error("FFmpeg render normalization failed: %s", _stderr(exc))
        return False


def constrain_render_duration(
    input_path: str,
    output_path: str,
    spec: RenderVideoSpec,
) -> bool:
    """Bound the muxed container to the Timeline duration without re-encoding."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-t",
        f"{spec.total_duration_seconds:.6f}",
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        output_path,
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=600, check=True)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        logger.error("FFmpeg render duration constraint failed: %s", _stderr(exc))
        return False


def probe_render_video(path: str) -> dict[str, Any]:
    """Return canonical container and primary-video stream metadata."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type,width,height,avg_frame_rate,nb_frames,duration",
        "-of",
        "json",
        path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True)
    payload = json.loads(result.stdout)
    video = next(
        (
            item
            for item in payload.get("streams", [])
            if item.get("codec_type") == "video"
        ),
        {},
    )
    return {
        "width": _maybe_int(video.get("width")),
        "height": _maybe_int(video.get("height")),
        "fps": _fraction_float(video.get("avg_frame_rate")),
        "frame_count": _maybe_int(video.get("nb_frames")),
        "video_duration_seconds": _positive_float(video.get("duration")),
        "duration_seconds": _positive_float(
            (payload.get("format") or {}).get("duration")
        ),
    }


def render_video_matches_spec(probe: dict[str, Any], spec: RenderVideoSpec) -> bool:
    duration = probe.get("duration_seconds") or probe.get("video_duration_seconds")
    return bool(
        probe.get("width") == spec.width
        and probe.get("height") == spec.height
        and abs(float(probe.get("fps") or 0) - spec.fps) < 0.01
        and probe.get("frame_count") == spec.total_frames
        and duration
        and abs(float(duration) - spec.total_duration_seconds) <= 1 / spec.fps
    )


def _positive_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _fraction_float(value: Any) -> float | None:
    try:
        numerator, denominator = str(value).split("/", 1)
        return float(numerator) / float(denominator)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _stderr(exc: BaseException) -> str:
    return str(getattr(exc, "stderr", None) or exc)
