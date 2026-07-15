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
    burn_subtitles_ffmpeg,
    compose_audio_segments_ffmpeg,
    concat_videos_ffmpeg,
    create_concat_file,
    replace_audio,
    trim_clip_to_duration,
)
from app.services.render.video_render_normalize import (
    constrain_render_duration,
    prepare_render_clips,
    probe_render_video,
    render_video_matches_spec,
)
from app.services.render.video_render_spec import RenderVideoSpec

logger = get_logger()

__all__ = [
    "VideoAudioSegment",
    "VideoClip",
    "VideoSubtitleCue",
    "burn_subtitles_ffmpeg",
    "compose_audio_segments_ffmpeg",
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


@dataclass
class VideoAudioSegment:
    """Represents one timeline-positioned audio segment."""

    url: str
    start_seconds: float
    end_seconds: float


@dataclass
class VideoSubtitleCue:
    """Represents one render subtitle cue."""

    text: str
    start_seconds: float
    end_seconds: float


async def concat_video_clips(
    clips: List[VideoClip],
    output_path: str,
    audio_url: Optional[str] = None,
    audio_segments: Optional[List[VideoAudioSegment]] = None,
    keep_original_audio: bool = True,
    subtitles: Optional[List[VideoSubtitleCue]] = None,
    render_spec: RenderVideoSpec | None = None,
) -> dict:
    """Concatenate video clips into single video.

    Args:
        clips: List of VideoClip objects with URLs and target durations
        output_path: Path for output video
        audio_url: Optional URL to external audio track (replaces video audio)
        audio_segments: Optional timeline-positioned audio segments to mix
        keep_original_audio: If True and no audio_url, keep video audio
        subtitles: Optional subtitle cues to burn into final video

    Returns:
        Dict with success status and metadata
    """
    work_dir = tempfile.mkdtemp(prefix="render_")
    try:
        logger.info(f"Downloading {len(clips)} clips...")
        raw_paths = await download_all_clips(clips, work_dir)

        logger.info("Normalizing clips to the render contract...")
        trimmed_paths, prepare_error = prepare_render_clips(
            raw_paths,
            [clip.target_duration_seconds for clip in clips],
            [clip.description for clip in clips],
            work_dir,
            render_spec,
        )
        if prepare_error:
            return {"success": False, "error": prepare_error}

        logger.info("Concatenating clips...")
        concat_output = os.path.join(work_dir, "concat.mp4")
        if not concat_videos_ffmpeg(trimmed_paths, concat_output, keep_original_audio):
            return {"success": False, "error": "Concatenation failed"}

        composed_output = concat_output
        audio_segment_items = audio_segments or []
        if audio_segment_items:
            logger.info("Composing %s audio segments...", len(audio_segment_items))
            audio_output = os.path.join(work_dir, "timeline_audio.m4a")
            if not await _compose_audio_segments(
                audio_segment_items, work_dir, audio_output
            ):
                return {"success": False, "error": "Audio segment composition failed"}
            replaced_output = os.path.join(work_dir, "with_audio.mp4")
            if not replace_audio(concat_output, audio_output, replaced_output):
                return {"success": False, "error": "Audio replacement failed"}
            composed_output = replaced_output
        elif audio_url:
            logger.info("Replacing audio track...")
            audio_data = await download_url(audio_url)
            audio_path = os.path.join(work_dir, "audio.mp3")
            with open(audio_path, "wb") as f:
                f.write(audio_data)

            audio_output = os.path.join(work_dir, "with_audio.mp4")
            if not replace_audio(concat_output, audio_path, audio_output):
                return {"success": False, "error": "Audio replacement failed"}
            composed_output = audio_output

        subtitle_cues = subtitles or []
        if subtitle_cues:
            logger.info("Burning %s subtitle cues...", len(subtitle_cues))
            subtitle_path = os.path.join(work_dir, "subtitles.srt")
            _write_srt(subtitle_cues, subtitle_path)
            if not burn_subtitles_ffmpeg(composed_output, subtitle_path, output_path):
                return {"success": False, "error": "Subtitle burn failed"}
        else:
            os.rename(composed_output, output_path)

        if render_spec:
            constrained_output = os.path.join(work_dir, "duration-bounded.mp4")
            if not constrain_render_duration(
                output_path, constrained_output, render_spec
            ):
                return {"success": False, "error": "Render duration constraint failed"}
            os.replace(constrained_output, output_path)

            probe = probe_render_video(output_path)
            if not render_video_matches_spec(probe, render_spec):
                return {
                    "success": False,
                    "error": f"Render output contract mismatch: {probe}",
                }
        else:
            probe = {}

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
            "has_replaced_audio": bool(audio_url or audio_segment_items),
            "audio_segment_count": len(audio_segment_items),
            "has_burned_subtitles": bool(subtitle_cues),
            "subtitle_count": len(subtitle_cues),
            "render_probe": probe,
        }

    finally:
        import shutil

        shutil.rmtree(work_dir, ignore_errors=True)


async def _compose_audio_segments(
    segments: List[VideoAudioSegment],
    work_dir: str,
    output_path: str,
) -> bool:
    audio_paths: list[str] = []
    starts: list[float] = []
    durations: list[float] = []
    for index, segment in enumerate(segments, start=1):
        data = await download_url(segment.url)
        audio_path = os.path.join(work_dir, f"audio-segment-{index}.mp3")
        with open(audio_path, "wb") as file:
            file.write(data)
        audio_paths.append(audio_path)
        starts.append(max(segment.start_seconds, 0))
        durations.append(max(segment.end_seconds - segment.start_seconds, 0.001))
    return compose_audio_segments_ffmpeg(audio_paths, starts, durations, output_path)


def _write_srt(cues: List[VideoSubtitleCue], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as file:
        for index, cue in enumerate(cues, start=1):
            file.write(f"{index}\n")
            file.write(
                f"{_srt_timestamp(cue.start_seconds)} --> "
                f"{_srt_timestamp(cue.end_seconds)}\n"
            )
            file.write(f"{_sanitize_subtitle_text(cue.text)}\n\n")


def _srt_timestamp(seconds: float) -> str:
    millis = max(round(seconds * 1000), 0)
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _sanitize_subtitle_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())
