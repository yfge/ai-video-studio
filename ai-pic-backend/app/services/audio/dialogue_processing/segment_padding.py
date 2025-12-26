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
    """Pad action/pause segments so the planned scene duration reaches target."""

    if target_duration_ms <= 0 or not segments:
        return segments

    dialogue_ms = _estimate_dialogue_duration_ms(dialogues)
    non_dialogue_ms = sum(
        int(seg.planned_duration_ms or 0)
        for seg in segments
        if seg.kind in {"action", "pause"}
    )
    planned_total_ms = dialogue_ms + non_dialogue_ms
    deficit_ms = target_duration_ms - planned_total_ms
    if deficit_ms <= 0:
        return segments

    if deficit_ms < min(1000, int(target_duration_ms * 0.05)):
        return segments

    padded = list(segments)

    def _extend(kind: str, max_ms: int) -> None:
        nonlocal deficit_ms, padded
        for idx, seg in enumerate(padded):
            if deficit_ms <= 0:
                return
            if seg.kind != kind:
                continue
            current = int(seg.planned_duration_ms or 0)
            capacity = max(0, max_ms - current)
            if capacity <= 0:
                continue
            add = min(deficit_ms, capacity)
            padded[idx] = PlannedSegment(
                kind=seg.kind,
                text=seg.text,
                speaker_name=seg.speaker_name,
                emotion=seg.emotion,
                action=seg.action,
                timing=seg.timing,
                planned_duration_ms=current + add,
            )
            deficit_ms -= add

    _extend("action", max_action_ms)
    _extend("pause", max_pause_ms)

    pad_text = "（转场留白）"
    while deficit_ms > 0:
        chunk = min(deficit_ms, max_action_ms)
        padded.append(
            PlannedSegment(
                kind="action",
                text=pad_text,
                timing="end",
                planned_duration_ms=int(chunk),
            )
        )
        deficit_ms -= chunk

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

