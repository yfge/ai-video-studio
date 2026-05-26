"""Rendered media evidence probes for provider-chain regression."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from scripts.harness._common import ensure_run_dir
from scripts.harness.provider_chain_payloads import scene_durations


def probe_render_output(args: argparse.Namespace, payload: dict[str, Any]) -> dict[str, Any]:
    render_job = payload.get("key_artifacts", {}).get("render_job") or {}
    output_url = str(render_job.get("output_url") or "")
    if not output_url.startswith(("http://", "https://")):
        raise RuntimeError("render_media_probe_missing_output_url")

    run_dir = ensure_run_dir(args.run_id)
    probe_path = run_dir / "render_ffprobe.json"
    frame_dir = run_dir / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)

    ffprobe = _ffprobe(output_url)
    probe_path.write_text(
        json.dumps(ffprobe, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    expected_duration = float(sum(scene_durations(args.mode)))
    format_duration = _format_duration(ffprobe)
    has_video_stream = _has_stream(ffprobe, "video")
    has_audio_stream = _has_stream(ffprobe, "audio")
    video_duration = _stream_duration(ffprobe, "video")
    audio_duration = _stream_duration(ffprobe, "audio")
    video_duration_for_check = video_duration or format_duration
    audio_duration_for_check = audio_duration or format_duration
    frames = _extract_scene_frames(
        output_url=output_url,
        mode=args.mode,
        frame_dir=frame_dir,
    )

    checks = {
        "has_video_stream": has_video_stream,
        "has_audio_stream": has_audio_stream,
        "format_duration_matches_timeline": _duration_close(
            format_duration, expected_duration
        ),
        "video_duration_matches_timeline": _duration_close(
            video_duration_for_check, expected_duration
        ),
        "audio_duration_matches_timeline": _duration_close(
            audio_duration_for_check, expected_duration
        ),
        "scene_frames_extracted": len(frames) == len(scene_durations(args.mode)),
    }
    artifact = {
        "output_url": output_url,
        "expected_duration_seconds": expected_duration,
        "format_duration_seconds": format_duration,
        "video_duration_seconds": video_duration,
        "audio_duration_seconds": audio_duration,
        "video_duration_check_seconds": video_duration_for_check,
        "audio_duration_check_seconds": audio_duration_for_check,
        "ffprobe_artifact": str(probe_path),
        "frame_artifacts": [str(path) for path in frames],
        "checks": checks,
        "ok": all(checks.values()),
    }
    payload["key_artifacts"]["render_media_probe"] = artifact
    if not artifact["ok"]:
        raise RuntimeError("render_media_probe_failed")
    return artifact


def _ffprobe(output_url: str) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=index,codec_type,codec_name,duration",
            "-of",
            "json",
            output_url,
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"render_media_ffprobe_failed: {completed.stderr.strip()}")
    return json.loads(completed.stdout or "{}")


def _extract_scene_frames(
    *,
    output_url: str,
    mode: str,
    frame_dir: Path,
) -> list[Path]:
    frames: list[Path] = []
    cursor = 0
    for index, duration in enumerate(scene_durations(mode), start=1):
        offset = cursor + min(2, max(duration / 2, 0.5))
        frame_path = frame_dir / f"render_scene_{index:02d}_{round(offset * 1000)}ms.jpg"
        completed = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                f"{offset:.3f}",
                "-i",
                output_url,
                "-frames:v",
                "1",
                str(frame_path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if completed.returncode != 0 or not frame_path.exists():
            raise RuntimeError(
                "render_media_frame_extract_failed: "
                f"scene={index} stderr={completed.stderr.strip()}"
            )
        frames.append(frame_path)
        cursor += duration
    return frames


def _has_stream(ffprobe: dict[str, Any], codec_type: str) -> bool:
    return any(
        isinstance(stream, dict) and stream.get("codec_type") == codec_type
        for stream in ffprobe.get("streams") or []
    )


def _stream_duration(ffprobe: dict[str, Any], codec_type: str) -> float | None:
    for stream in ffprobe.get("streams") or []:
        if not isinstance(stream, dict) or stream.get("codec_type") != codec_type:
            continue
        return _maybe_float(stream.get("duration"))
    return None


def _format_duration(ffprobe: dict[str, Any]) -> float | None:
    fmt = ffprobe.get("format")
    if not isinstance(fmt, dict):
        return None
    return _maybe_float(fmt.get("duration"))


def _maybe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _duration_close(actual: float | None, expected: float) -> bool:
    if actual is None:
        return False
    return expected - 1 <= actual <= expected + 2
