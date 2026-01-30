"""Video concatenation utilities using ffmpeg.

Handles frame-level video clips concatenation with optional audio replacement.
"""

import asyncio
import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import List, Optional

import aiohttp

from app.core.logging import get_logger

logger = get_logger()


@dataclass
class VideoClip:
    """Represents a video clip for concatenation."""

    url: str
    target_duration_seconds: float
    frame_number: int
    description: Optional[str] = None


async def download_video(url: str, session: aiohttp.ClientSession) -> bytes:
    """Download video from URL."""
    async with session.get(url) as resp:
        if resp.status != 200:
            raise ValueError(f"Failed to download video: {url} (status={resp.status})")
        return await resp.read()


async def download_all_clips(
    clips: List[VideoClip],
    work_dir: str,
) -> List[str]:
    """Download all video clips to work directory.

    Returns list of local file paths in order.
    """
    paths = []
    async with aiohttp.ClientSession() as session:
        for i, clip in enumerate(clips):
            try:
                data = await download_video(clip.url, session)
                path = os.path.join(work_dir, f"clip_{i:03d}.mp4")
                with open(path, "wb") as f:
                    f.write(data)
                paths.append(path)
                logger.info(f"Downloaded clip {i+1}/{len(clips)}: {len(data)} bytes")
            except Exception as e:
                logger.error(f"Failed to download clip {i}: {e}")
                raise
    return paths


def trim_clip_to_duration(
    input_path: str,
    output_path: str,
    target_duration: float,
) -> bool:
    """Trim or pad video clip to target duration using ffmpeg.

    Returns True if successful.
    """
    # First, get actual duration
    probe_cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        input_path,
    ]
    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        actual_duration = float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Could not probe duration: {e}, using target")
        actual_duration = target_duration

    if abs(actual_duration - target_duration) < 0.1:
        # Close enough, just copy
        os.rename(input_path, output_path)
        return True

    if actual_duration > target_duration:
        # Trim to target
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-t", str(target_duration),
            "-c", "copy",
            output_path,
        ]
    else:
        # Pad with freeze frame (tpad filter)
        pad_duration = target_duration - actual_duration
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"tpad=stop_mode=clone:stop_duration={pad_duration}",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "copy",
            output_path,
        ]

    try:
        subprocess.run(cmd, capture_output=True, timeout=120, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg trim failed: {e.stderr}")
        return False


def create_concat_file(clip_paths: List[str], concat_file_path: str) -> None:
    """Create ffmpeg concat demuxer file."""
    with open(concat_file_path, "w") as f:
        for path in clip_paths:
            # Escape single quotes in path
            escaped = path.replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")


def concat_videos_ffmpeg(
    clip_paths: List[str],
    output_path: str,
    keep_audio: bool = True,
) -> bool:
    """Concatenate videos using ffmpeg concat demuxer.

    Args:
        clip_paths: List of video file paths to concatenate
        output_path: Output file path
        keep_audio: Whether to keep audio from videos

    Returns:
        True if successful
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        concat_file = f.name
        create_concat_file(clip_paths, concat_file)

    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
        ]
        if keep_audio:
            cmd.extend(["-c", "copy"])
        else:
            cmd.extend(["-c:v", "copy", "-an"])
        cmd.append(output_path)

        subprocess.run(cmd, capture_output=True, timeout=600, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg concat failed: {e.stderr}")
        return False
    finally:
        if os.path.exists(concat_file):
            os.unlink(concat_file)


def replace_audio(
    video_path: str,
    audio_path: str,
    output_path: str,
) -> bool:
    """Replace video audio track with external audio file.

    Args:
        video_path: Input video file
        audio_path: Audio file to use (mp3/wav)
        output_path: Output video file

    Returns:
        True if successful
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path,
    ]

    try:
        subprocess.run(cmd, capture_output=True, timeout=600, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg audio replace failed: {e.stderr}")
        return False


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
        # Download all clips
        logger.info(f"Downloading {len(clips)} clips...")
        raw_paths = await download_all_clips(clips, work_dir)

        # Trim/pad each clip to target duration
        logger.info("Trimming clips to target durations...")
        trimmed_paths = []
        for i, (raw_path, clip) in enumerate(zip(raw_paths, clips)):
            trimmed_path = os.path.join(work_dir, f"trimmed_{i:03d}.mp4")
            if trim_clip_to_duration(raw_path, trimmed_path, clip.target_duration_seconds):
                trimmed_paths.append(trimmed_path)
            else:
                # Fallback: use raw clip
                trimmed_paths.append(raw_path)

        # Concatenate all clips
        logger.info("Concatenating clips...")
        concat_output = os.path.join(work_dir, "concat.mp4")
        if not concat_videos_ffmpeg(trimmed_paths, concat_output, keep_original_audio):
            return {"success": False, "error": "Concatenation failed"}

        # Replace audio if requested
        if audio_url:
            logger.info("Replacing audio track...")
            async with aiohttp.ClientSession() as session:
                audio_data = await download_video(audio_url, session)
            audio_path = os.path.join(work_dir, "audio.mp3")
            with open(audio_path, "wb") as f:
                f.write(audio_data)

            if not replace_audio(concat_output, audio_path, output_path):
                return {"success": False, "error": "Audio replacement failed"}
        else:
            os.rename(concat_output, output_path)

        # Get output duration
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            output_path,
        ]
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
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
        # Cleanup work directory
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)
