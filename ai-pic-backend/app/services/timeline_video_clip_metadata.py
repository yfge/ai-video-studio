"""Attach beat-window lineage to one Timeline video clip."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def attach_video_window_metadata(
    clip: dict[str, Any],
    beat: dict[str, Any],
    *,
    part_index: int,
    clip_id_factory: Callable[..., str],
) -> None:
    source_ranges = beat.get("source_beat_ranges") or []
    source_clip_ids = [
        clip_id_factory(
            track_type="video",
            scene_id=source_range.get("scene_id"),
            beat_id=source_range.get("beat_id"),
            ordinal=int(source_range.get("ordinal")),
        )
        for source_range in source_ranges
        if isinstance(source_range, dict) and source_range.get("ordinal") is not None
    ]
    clip.update(
        {
            "source_clip_ids": list(dict.fromkeys(source_clip_ids)),
            "grouped_beat_ids": beat.get("grouped_beat_ids") or [],
            "source_beat_types": beat.get("source_beat_types") or [],
            "source_beat_ranges": source_ranges,
            "texts": beat.get("texts") or [],
            "video_part_index": part_index,
            "video_segmentation_strategy": beat.get("video_segmentation_strategy"),
            "asset_ref": None,
            "placeholder": True,
        }
    )
    clip["source_refs"].update(
        {
            "source_clip_ids": clip["source_clip_ids"],
            "grouped_beat_ids": clip["grouped_beat_ids"],
            "source_beat_ranges": source_ranges,
            "video_part_index": part_index,
            "video_segmentation_strategy": clip["video_segmentation_strategy"],
        }
    )
