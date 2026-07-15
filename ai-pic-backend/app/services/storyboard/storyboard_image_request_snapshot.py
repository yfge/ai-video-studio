from __future__ import annotations

import copy
from typing import Any

IMAGE_GENERATION_OUTPUT_FIELDS = frozenset(
    {
        "image_url",
        "image_urls",
        "image_url_original",
        "start_image_url",
        "start_image_urls",
        "start_image_url_original",
        "end_image_url",
        "end_image_urls",
        "end_image_url_original",
        "image_gen",
        "start_image_gen",
        "end_image_gen",
        "image_generation",
        "storyboard_prompt_v2",
        "canvas_candidate_lineage",
        "storyboard_image_task_checkpoint",
    }
)


def storyboard_image_worker_frame_snapshot(
    frame: dict[str, Any], frame_index: int
) -> dict[str, Any]:
    """Capture image worker inputs without mutable checkpoint outputs."""
    return {
        "frame_index": frame_index,
        "frame": {
            key: copy.deepcopy(value)
            for key, value in frame.items()
            if key not in IMAGE_GENERATION_OUTPUT_FIELDS
        },
    }
