"""Video concatenation utilities using ffmpeg.

Handles frame-level video clips concatenation with optional audio replacement.
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import List, Optional

from app.core.logging import get_logger
from app.services.render.video_download import download_all_clips, download_url
from app.services.render.video_ffmpeg import (
    concat_videos_ffmpeg,
    create_concat_file,
    replace_audio,
    trim_clip_to_duration,
)

logger = get_logger()

__all__ = [
    "VideoClip",
    "concat_video_clips",
    "concat_videos_ffmpeg",
    "create_concat_file",
    "replace_audio",
    "trim_clip_to_duration",
]


@dataclass
class VideoClip:
    """Represents a video clip for concatenation."""

    url: str
    target_duration_seconds: float
    frame_number: int
    description: Optional[str] = None


async def concat_video_clips(
    clips: List[VideoClip],
    output_path: str,
    audio_url: Optional[str] = None,
    keep_original_audio: bool = True,
) -> dict:
    """Concatenate video clips into single video.

    Args:
        clips: List of VideoClip objects with URLs and target durations
        output_path: Path for output video
        audio_url: Optional URL to external audio track (replaces video audio)
        keep_original_audio: If True and no audio_url, keep video audio

    Returns:
        Dict with success status and metadata
    """
    work_dir = tempfile.mkdtemp(prefix="render_")
    try:
        logger.info(f"Downloading {len(clips)} clips...")
        raw_paths = await download_all_clips(clips, work_dir)

        logger.info("Trimming clips to target durations...")
        trimmed_paths = []
        for i, (raw_path, clip) in enumerate(zip(raw_paths, clips)):
            trimmed_path = os.path.join(work_dir, f"trimmed_{i:03d}.mp4")
            if trim_clip_to_duration(
                raw_path, trimmed_path, clip.target_duration_seconds
            ):
                trimmed_paths.append(trimmed_path)
            else:
                trimmed_paths.append(raw_path)

        logger.info("Concatenating clips...")
        concat_output = os.path.join(work_dir, "concat.mp4")
        if not concat_videos_ffmpeg(trimmed_paths, concat_output, keep_original_audio):
            return {"success": False, "error": "Concatenation failed"}

        if audio_url:
            logger.info("Replacing audio track...")
            audio_data = await download_url(audio_url)
            audio_path = os.path.join(work_dir, "audio.mp3")
            with open(audio_path, "wb") as f:
                f.write(audio_data)

            if not replace_audio(concat_output, audio_path, output_path):
                return {"success": False, "error": "Audio replacement failed"}
        else:
            os.rename(concat_output, output_path)

        probe_cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            output_path,
        ]
        try:
            result = subprocess.run(
                probe_cmd, capture_output=True, text=True, timeout=30
            )
            duration = float(result.stdout.strip())
        except Exception:
            duration = sum(c.target_duration_seconds for c in clips)

        return {
            "success": True,
            "output_path": output_path,
            "duration_seconds": duration,
            "frame_count": len(clips),
            "has_replaced_audio": bool(audio_url),
        }

    finally:
        import shutil

        shutil.rmtree(work_dir, ignore_errors=True)
