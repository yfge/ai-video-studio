"""Shared Timeline video-window constants and Spec metadata."""

from typing import Any

VIDEO_SEGMENTATION_STRATEGY = "beat_window_v2"
VIDEO_MIN_DURATION_MS = 5000
VIDEO_TARGET_DURATION_MS = 6000
VIDEO_MAX_DURATION_MS = 8000
VIDEO_TAIL_MIN_DURATION_MS = 3000


def video_segmentation_metadata() -> dict[str, Any]:
    return {
        "strategy": VIDEO_SEGMENTATION_STRATEGY,
        "min_duration_ms": VIDEO_MIN_DURATION_MS,
        "target_duration_ms": VIDEO_TARGET_DURATION_MS,
        "max_duration_ms": VIDEO_MAX_DURATION_MS,
        "tail_min_duration_ms": VIDEO_TAIL_MIN_DURATION_MS,
    }
