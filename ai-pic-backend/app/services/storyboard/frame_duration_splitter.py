"""
Frame duration splitter for storyboard generation.

Splits long storyboard frames at beat boundaries when they exceed video model
max duration, and merges short consecutive beats when below min duration.

This ensures storyboard frames align with video generation capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence
from uuid import uuid4

from app.core.logging import get_logger

logger = get_logger()

# Default video capability constraints (from video_capabilities.py)
DEFAULT_MAX_DURATION_SECONDS = 8.0
DEFAULT_MIN_DURATION_SECONDS = 4.0


@dataclass
class SplitResult:
    """Result of frame splitting operation."""

    frames: List[dict[str, Any]]
    splits_performed: int
    merges_performed: int
    audit_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "frame_count": len(self.frames),
            "splits_performed": self.splits_performed,
            "merges_performed": self.merges_performed,
            "audit_notes": self.audit_notes,
        }


def split_long_frames(
    frames: Sequence[dict[str, Any]],
    *,
    max_duration_seconds: float = DEFAULT_MAX_DURATION_SECONDS,
    min_duration_seconds: float = DEFAULT_MIN_DURATION_SECONDS,
) -> SplitResult:
    """
    Split frames that exceed max_duration_seconds.

    Long frames are split into segments of max_duration_seconds. Split frames
    are linked via parent_frame_id and split_index for UI tracking.

    Args:
        frames: List of storyboard frame dictionaries.
        max_duration_seconds: Maximum allowed frame duration.
        min_duration_seconds: Minimum frame duration (used for split segments).

    Returns:
        SplitResult with processed frames and audit info.
    """
    if not frames:
        return SplitResult(frames=[], splits_performed=0, merges_performed=0)

    result_frames: List[dict[str, Any]] = []
    splits_performed = 0
    audit_notes: List[str] = []

    for frame in frames:
        if not isinstance(frame, dict):
            continue

        duration = _get_duration(frame)
        if duration <= max_duration_seconds:
            result_frames.append(frame)
            continue

        # Frame exceeds max duration - split it
        original_frame_id = frame.get("frame_id") or str(uuid4())
        start_ms = frame.get("start_ms") or 0
        end_ms = frame.get("end_ms") or int(start_ms + duration * 1000)
        total_ms = end_ms - start_ms

        # Calculate number of segments needed
        max_ms = int(max_duration_seconds * 1000)
        num_segments = (total_ms + max_ms - 1) // max_ms  # Ceiling division

        audit_notes.append(
            f"Split frame {original_frame_id} ({duration:.1f}s) into {num_segments} segments"
        )

        # Create split segments
        cursor_ms = start_ms
        segments_created = 0
        absorbed_tiny_segment = False
        for i in range(num_segments):
            segment_start = cursor_ms
            segment_end = min(cursor_ms + max_ms, end_ms)
            segment_duration = (segment_end - segment_start) / 1000.0

            # Don't create tiny segments at the end
            if segment_duration < min_duration_seconds * 0.5 and i > 0:
                # Extend previous segment instead
                if result_frames:
                    prev = result_frames[-1]
                    prev["end_ms"] = segment_end
                    prev["duration_seconds"] = round(
                        (segment_end - prev.get("start_ms", segment_start)) / 1000.0, 3
                    )
                    # If only one segment was created and we absorbed the rest,
                    # remove split metadata since it's not actually split
                    if segments_created == 1:
                        prev.pop("parent_frame_id", None)
                        prev.pop("split_index", None)
                        prev.pop("total_splits", None)
                        prev.pop("beat_range", None)
                        absorbed_tiny_segment = True
                break

            split_frame = _create_split_frame(
                original_frame=frame,
                parent_frame_id=original_frame_id,
                split_index=i,
                total_splits=num_segments,
                segment_start_ms=segment_start,
                segment_end_ms=segment_end,
                frame_number=len(result_frames) + 1,
            )
            result_frames.append(split_frame)
            cursor_ms = segment_end
            segments_created += 1

        # Only count as split if we actually created multiple segments
        if segments_created > 1:
            splits_performed += segments_created - 1
            # Update total_splits to reflect actual segments created
            for fr in result_frames[-segments_created:]:
                fr["total_splits"] = segments_created
        elif absorbed_tiny_segment:
            # Update audit note to reflect absorption
            if audit_notes and audit_notes[-1].startswith(f"Split frame {original_frame_id}"):
                audit_notes[-1] = (
                    f"Frame {original_frame_id} ({duration:.1f}s) kept as single frame "
                    f"(remainder too short to split)"
                )

    # Renumber frames
    for i, frame in enumerate(result_frames, start=1):
        frame["frame_number"] = i

    logger.info(
        "frame_duration_split_completed",
        extra={
            "input_count": len(frames),
            "output_count": len(result_frames),
            "splits_performed": splits_performed,
            "max_duration": max_duration_seconds,
        },
    )

    return SplitResult(
        frames=result_frames,
        splits_performed=splits_performed,
        merges_performed=0,
        audit_notes=audit_notes,
    )


def merge_short_frames(
    frames: Sequence[dict[str, Any]],
    *,
    min_duration_seconds: float = DEFAULT_MIN_DURATION_SECONDS,
    merge_types: tuple[str, ...] = ("pause", "action"),
) -> SplitResult:
    """
    Merge consecutive short frames of mergeable types.

    Short pause/action beats are merged with adjacent beats to form longer
    frames that meet minimum duration requirements.

    Args:
        frames: List of storyboard frame dictionaries.
        min_duration_seconds: Minimum frame duration threshold.
        merge_types: Beat types eligible for merging.

    Returns:
        SplitResult with merged frames and audit info.
    """
    if not frames:
        return SplitResult(frames=[], splits_performed=0, merges_performed=0)

    result_frames: List[dict[str, Any]] = []
    merges_performed = 0
    audit_notes: List[str] = []

    pending: Optional[dict[str, Any]] = None

    for frame in frames:
        if not isinstance(frame, dict):
            continue

        duration = _get_duration(frame)
        beat_type = _infer_beat_type(frame)
        is_mergeable = beat_type in merge_types and duration < min_duration_seconds

        if pending is None:
            if is_mergeable:
                # Start accumulating mergeable frames
                pending = dict(frame)
                pending["merged_beat_ids"] = [frame.get("frame_id")]
            else:
                result_frames.append(frame)
            continue

        # We have a pending frame to potentially merge
        pending_scene = pending.get("scene_number")
        current_scene = frame.get("scene_number")
        pending_end = pending.get("end_ms", 0)
        current_start = frame.get("start_ms", 0)

        # Check if we can merge: same scene and continuous timeline
        can_merge = (
            pending_scene == current_scene
            and abs(pending_end - current_start) < 100  # 100ms tolerance
        )

        if can_merge and is_mergeable:
            # Merge into pending
            pending["end_ms"] = frame.get("end_ms", pending_end)
            new_duration = (pending["end_ms"] - pending.get("start_ms", 0)) / 1000.0
            pending["duration_seconds"] = round(new_duration, 3)

            # Track merged beats
            merged_ids = pending.get("merged_beat_ids", [])
            merged_ids.append(frame.get("frame_id"))
            pending["merged_beat_ids"] = merged_ids

            # Append description if action/dialogue
            if beat_type != "pause" and frame.get("description"):
                pending_desc = pending.get("description", "")
                frame_desc = frame.get("description", "")
                if frame_desc and frame_desc not in pending_desc:
                    pending["description"] = f"{pending_desc}；{frame_desc}".strip("；")

            merges_performed += 1
            continue

        # Cannot merge - flush pending and process current
        result_frames.append(pending)
        pending = None

        if is_mergeable:
            pending = dict(frame)
            pending["merged_beat_ids"] = [frame.get("frame_id")]
        else:
            result_frames.append(frame)

    # Flush remaining pending frame
    if pending is not None:
        result_frames.append(pending)

    # Renumber frames
    for i, frame in enumerate(result_frames, start=1):
        frame["frame_number"] = i

    if merges_performed > 0:
        audit_notes.append(f"Merged {merges_performed} short frames")
        logger.info(
            "frame_duration_merge_completed",
            extra={
                "input_count": len(frames),
                "output_count": len(result_frames),
                "merges_performed": merges_performed,
                "min_duration": min_duration_seconds,
            },
        )

    return SplitResult(
        frames=result_frames,
        splits_performed=0,
        merges_performed=merges_performed,
        audit_notes=audit_notes,
    )


def adjust_frame_durations(
    frames: Sequence[dict[str, Any]],
    *,
    max_duration_seconds: float = DEFAULT_MAX_DURATION_SECONDS,
    min_duration_seconds: float = DEFAULT_MIN_DURATION_SECONDS,
    merge_types: tuple[str, ...] = ("pause", "action"),
) -> SplitResult:
    """
    Apply both splitting and merging to optimize frame durations.

    This is the main entry point for frame duration adjustment. It first merges
    short frames, then splits long frames, ensuring all frames fall within
    the min/max duration constraints.

    Args:
        frames: List of storyboard frame dictionaries.
        max_duration_seconds: Maximum allowed frame duration.
        min_duration_seconds: Minimum frame duration threshold.
        merge_types: Beat types eligible for merging.

    Returns:
        SplitResult with adjusted frames and combined audit info.
    """
    # First merge short frames
    merge_result = merge_short_frames(
        frames,
        min_duration_seconds=min_duration_seconds,
        merge_types=merge_types,
    )

    # Then split long frames
    split_result = split_long_frames(
        merge_result.frames,
        max_duration_seconds=max_duration_seconds,
        min_duration_seconds=min_duration_seconds,
    )

    return SplitResult(
        frames=split_result.frames,
        splits_performed=split_result.splits_performed,
        merges_performed=merge_result.merges_performed,
        audit_notes=merge_result.audit_notes + split_result.audit_notes,
    )


def _get_duration(frame: dict[str, Any]) -> float:
    """Get frame duration in seconds."""
    duration = frame.get("duration_seconds")
    if duration is not None:
        try:
            return float(duration)
        except (TypeError, ValueError):
            pass

    start_ms = frame.get("start_ms")
    end_ms = frame.get("end_ms")
    if start_ms is not None and end_ms is not None:
        try:
            return (float(end_ms) - float(start_ms)) / 1000.0
        except (TypeError, ValueError):
            pass

    return 0.0


def _infer_beat_type(frame: dict[str, Any]) -> str:
    """Infer beat type from frame data."""
    beat_type = frame.get("beat_type")
    if beat_type:
        return str(beat_type).lower()

    description = frame.get("description", "")
    if "停顿" in description or "pause" in description.lower():
        return "pause"
    if "动作" in description or "action" in description.lower():
        return "action"

    return "dialogue"


def _create_split_frame(
    *,
    original_frame: dict[str, Any],
    parent_frame_id: str,
    split_index: int,
    total_splits: int,
    segment_start_ms: int,
    segment_end_ms: int,
    frame_number: int,
) -> dict[str, Any]:
    """Create a split frame segment with linkage metadata."""
    segment_duration = (segment_end_ms - segment_start_ms) / 1000.0

    frame = {
        "frame_id": str(uuid4()),
        "frame_number": frame_number,
        "scene_number": original_frame.get("scene_number"),
        "scene_index": original_frame.get("scene_index"),
        "description": original_frame.get("description", ""),
        "duration_seconds": round(segment_duration, 3),
        "generation_source": "split_from_timeline",
        "generation_method": "duration_split",
        "status": "draft",
        "start_ms": segment_start_ms,
        "end_ms": segment_end_ms,
        # Linkage metadata for tracking
        "parent_frame_id": parent_frame_id,
        "split_index": split_index,
        "total_splits": total_splits,
        "beat_range": f"{segment_start_ms}-{segment_end_ms}",
    }

    # Copy optional fields from original
    for key in ("shot_type", "camera_movement", "composition", "ai_prompt"):
        if key in original_frame:
            frame[key] = original_frame[key]

    # Add continuation marker to description for middle/end segments
    if split_index > 0:
        desc = frame.get("description", "")
        if desc and not desc.startswith("（续）"):
            frame["description"] = f"（续）{desc}"

    return frame


__all__ = [
    "SplitResult",
    "split_long_frames",
    "merge_short_frames",
    "adjust_frame_durations",
    "DEFAULT_MAX_DURATION_SECONDS",
    "DEFAULT_MIN_DURATION_SECONDS",
]
