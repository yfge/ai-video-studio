"""FFmpeg helpers for render video composition."""

from __future__ import annotations

import os
import subprocess
import tempfile
from typing import List

from app.core.logging import get_logger

logger = get_logger()


def trim_clip_to_duration(
    input_path: str,
    output_path: str,
    target_duration: float,
) -> bool:
    """Trim or pad video clip to target duration using ffmpeg."""
    probe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "csv=p=0",
        input_path,
    ]
    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        actual_duration = float(result.stdout.strip())
    except Exception as exc:
        logger.warning("Could not probe duration: %s, using target", exc)
        actual_duration = target_duration

    if abs(actual_duration - target_duration) < 0.1:
        os.rename(input_path, output_path)
        return True

    if actual_duration > target_duration:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-t",
            str(target_duration),
            "-c",
            "copy",
            output_path,
        ]
    else:
        pad_duration = target_duration - actual_duration
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-vf",
            f"tpad=stop_mode=clone:stop_duration={pad_duration}",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-c:a",
            "copy",
            output_path,
        ]

    try:
        subprocess.run(cmd, capture_output=True, timeout=120, check=True)
        return True
    except subprocess.CalledProcessError as exc:
        logger.error("FFmpeg trim failed: %s", exc.stderr)
        return False


def create_concat_file(clip_paths: List[str], concat_file_path: str) -> None:
    """Create ffmpeg concat demuxer file."""
    with open(concat_file_path, "w") as file:
        for path in clip_paths:
            escaped = path.replace("'", "'\\''")
            file.write(f"file '{escaped}'\n")


def concat_videos_ffmpeg(
    clip_paths: List[str],
    output_path: str,
    keep_audio: bool = True,
) -> bool:
    """Concatenate videos using ffmpeg concat demuxer."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as file:
        concat_file = file.name
        create_concat_file(clip_paths, concat_file)

    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file,
        ]
        cmd.extend(["-c", "copy"] if keep_audio else ["-c:v", "copy", "-an"])
        cmd.append(output_path)
        subprocess.run(cmd, capture_output=True, timeout=600, check=True)
        return True
    except subprocess.CalledProcessError as exc:
        logger.error("FFmpeg concat failed: %s", exc.stderr)
        return False
    finally:
        if os.path.exists(concat_file):
            os.unlink(concat_file)


def replace_audio(
    video_path: str,
    audio_path: str,
    output_path: str,
) -> bool:
    """Replace video audio track with external audio and keep video duration."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-filter_complex",
        "[1:a]apad[a]",
        "-map",
        "0:v:0",
        "-map",
        "[a]",
        "-c:a",
        "aac",
        "-shortest",
        output_path,
    ]

    try:
        subprocess.run(cmd, capture_output=True, timeout=600, check=True)
        return True
    except subprocess.CalledProcessError as exc:
        logger.error("FFmpeg audio replace failed: %s", exc.stderr)
        return False


def burn_subtitles_ffmpeg(
    video_path: str,
    subtitle_path: str,
    output_path: str,
) -> bool:
    """Burn SRT subtitles into a video file."""
    style = (
        "FontSize=24,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=2,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginV=70"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vf",
        f"subtitles={_escape_subtitle_filter_path(subtitle_path)}:force_style='{style}'",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-c:a",
        "copy",
        output_path,
    ]

    try:
        subprocess.run(cmd, capture_output=True, timeout=600, check=True)
        return True
    except subprocess.CalledProcessError as exc:
        logger.error("FFmpeg subtitle burn failed: %s", exc.stderr)
        return False


def _escape_subtitle_filter_path(path: str) -> str:
    return path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
