"""Padding utilities to align planned segments with target duration."""

from __future__ import annotations

from typing import Any, Sequence

from app.core.logging import get_logger

from .segment_models import PlannedSegment
from .text_utils import looks_like_silence

logger = get_logger()


def _estimate_dialogue_duration_ms(dialogues: Sequence[dict[str, Any]]) -> int:
    """Estimate total dialogue duration from provided dialogue dicts.

    Prefer actual durations (from TTS), fallback to estimated durations when present.
    """

    total_ms = 0
    for dlg in dialogues:
        if not isinstance(dlg, dict):
            continue
        content = str(dlg.get("content") or "")
        if looks_like_silence(content):
            continue
        duration = dlg.get("actual_duration_ms")
        if duration is None:
            duration = dlg.get("estimated_duration_ms")
        try:
            total_ms += int(duration) if duration is not None else 0
        except Exception:
            continue
    return max(0, total_ms)


def _pad_segments_to_target_duration_ms(
    *,
    segments: list[PlannedSegment],
    dialogues: Sequence[dict[str, Any]],
    target_duration_ms: int,
    scene_context: dict[str, Any] | None = None,
    max_action_ms: int = 15000,
    max_pause_ms: int = 10000,
) -> list[PlannedSegment]:
    """Pad or trim action/pause segments so the planned scene duration matches target."""

    if target_duration_ms <= 0 or not segments:
        return segments

    dialogue_ms = _estimate_dialogue_duration_ms(dialogues)
    non_dialogue_ms = sum(
        int(seg.planned_duration_ms or 0)
        for seg in segments
        if seg.kind in {"action", "pause"}
    )
    planned_total_ms = dialogue_ms + non_dialogue_ms
    delta_ms = target_duration_ms - planned_total_ms
    if delta_ms == 0:
        return segments

    if abs(delta_ms) < min(1000, int(target_duration_ms * 0.05)):
        return segments

    padded = list(segments)

    # If we overshoot the target, trim non-dialogue segments first.
    if delta_ms < 0:
        overflow_ms = -delta_ms

        def _trim(kind: str) -> None:
            nonlocal overflow_ms, padded
            next_segments: list[PlannedSegment] = []
            for seg in padded:
                if overflow_ms <= 0:
                    next_segments.append(seg)
                    continue
                if seg.kind != kind or seg.planned_duration_ms is None:
                    next_segments.append(seg)
                    continue
                current = int(seg.planned_duration_ms or 0)
                if current <= 0:
                    continue
                remove = min(overflow_ms, current)
                new_ms = current - remove
                overflow_ms -= remove
                if new_ms <= 0:
                    # Drop the segment entirely to avoid creating 0ms beats.
                    continue
                next_segments.append(
                    PlannedSegment(
                        kind=seg.kind,
                        text=seg.text,
                        speaker_name=seg.speaker_name,
                        emotion=seg.emotion,
                        action=seg.action,
                        timing=seg.timing,
                        planned_duration_ms=new_ms,
                    )
                )
            padded = next_segments

        _trim("pause")
        _trim("action")

        return padded

    def _extend(kind: str, max_ms: int) -> None:
        nonlocal delta_ms, padded
        for idx, seg in enumerate(padded):
            if delta_ms <= 0:
                return
            if seg.kind != kind:
                continue
            current = int(seg.planned_duration_ms or 0)
            capacity = max(0, max_ms - current)
            if capacity <= 0:
                continue
            add = min(delta_ms, capacity)
            padded[idx] = PlannedSegment(
                kind=seg.kind,
                text=seg.text,
                speaker_name=seg.speaker_name,
                emotion=seg.emotion,
                action=seg.action,
                timing=seg.timing,
                planned_duration_ms=current + add,
            )
            delta_ms -= add

    _extend("action", max_action_ms)
    _extend("pause", max_pause_ms)

    pad_text = "（转场留白）"
    while delta_ms > 0:
        chunk = min(delta_ms, max_action_ms)
        padded.append(
            PlannedSegment(
                kind="action",
                text=pad_text,
                timing="end",
                planned_duration_ms=int(chunk),
            )
        )
        delta_ms -= chunk

    if scene_context:
        try:
            scene_id = scene_context.get("scene_id")
            scene_number = scene_context.get("scene_number")
        except Exception:
            scene_id = None
            scene_number = None
        new_non_dialogue_ms = sum(
            int(seg.planned_duration_ms or 0)
            for seg in padded
            if seg.kind in {"action", "pause"}
        )
        new_total_ms = dialogue_ms + new_non_dialogue_ms
        logger.info(
            "Padded scene segments to target duration",
            extra={
                "scene_id": scene_id,
                "scene_number": scene_number,
                "target_ms": target_duration_ms,
                "before_ms": planned_total_ms,
                "after_ms": new_total_ms,
                "added_ms": new_total_ms - planned_total_ms,
            },
        )

    return padded
