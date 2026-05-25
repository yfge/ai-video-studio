"""Compatibility helpers for the historical dialogue audio service facade."""

from __future__ import annotations

from typing import Any, Sequence

from app.services.audio.dialogue_processing.segment_models import PlannedSegment
from app.services.audio.dialogue_service_text_compat import looks_like_silence


def plan_scene_segments(
    *,
    dialogues: Sequence[dict[str, Any]],
    stage_directions: Sequence[dict[str, Any]],
    pause_after_dialogue_ms: int = 300,
    action_base_ms: int = 800,
    action_per_char_ms: int = 20,
    action_max_ms: int = 3000,
) -> list[PlannedSegment]:
    """Build an ordered scene segment plan for historical imports."""
    stages_start: list[str] = []
    stages_mid: list[str] = []
    stages_end: list[str] = []
    for sd in stage_directions:
        if not isinstance(sd, dict):
            continue
        content = str(sd.get("content") or "").strip()
        if not content:
            continue
        timing = str(sd.get("timing") or "mid").strip().lower()
        if timing in {"start", "begin", "opening"}:
            stages_start.append(content)
        elif timing in {"end", "closing"}:
            stages_end.append(content)
        else:
            stages_mid.append(content)

    planned: list[PlannedSegment] = []

    def _action_duration_ms(content: str) -> int:
        length = len(content)
        return min(
            action_max_ms,
            max(action_base_ms, action_base_ms + length * action_per_char_ms),
        )

    for content in stages_start:
        planned.append(
            PlannedSegment(
                kind="action",
                text=content,
                timing="start",
                planned_duration_ms=_action_duration_ms(content),
            )
        )

    mid_inserted = False

    for _idx, dlg in enumerate(dialogues):
        speaker = str(dlg.get("character") or "旁白")
        content = str(dlg.get("content") or "").strip()
        emotion = (
            str(dlg.get("emotion") or "").strip()
            if isinstance(dlg.get("emotion"), str)
            else None
        )
        emotion = emotion or None
        action = (
            str(dlg.get("action") or "").strip()
            if isinstance(dlg.get("action"), str)
            else None
        )
        action = action or None
        if looks_like_silence(content):
            planned.append(
                PlannedSegment(
                    kind="pause",
                    text=content or "…",
                    speaker_name=speaker,
                    emotion=emotion,
                    action=action,
                    planned_duration_ms=800,
                )
            )
        else:
            planned.append(
                PlannedSegment(
                    kind="dialogue",
                    text=content,
                    speaker_name=speaker,
                    emotion=emotion,
                    action=action,
                )
            )
        planned.append(
            PlannedSegment(
                kind="pause",
                text="",
                planned_duration_ms=pause_after_dialogue_ms,
            )
        )

        if not mid_inserted and stages_mid:
            for content_mid in stages_mid:
                planned.append(
                    PlannedSegment(
                        kind="action",
                        text=content_mid,
                        timing="mid",
                        planned_duration_ms=_action_duration_ms(content_mid),
                    )
                )
                planned.append(
                    PlannedSegment(
                        kind="pause",
                        text="",
                        planned_duration_ms=pause_after_dialogue_ms,
                    )
                )
            mid_inserted = True

    if stages_mid and not mid_inserted:
        for content_mid in stages_mid:
            planned.append(
                PlannedSegment(
                    kind="action",
                    text=content_mid,
                    timing="mid",
                    planned_duration_ms=_action_duration_ms(content_mid),
                )
            )
            planned.append(
                PlannedSegment(
                    kind="pause",
                    text="",
                    planned_duration_ms=pause_after_dialogue_ms,
                )
            )

    for content in stages_end:
        planned.append(
            PlannedSegment(
                kind="action",
                text=content,
                timing="end",
                planned_duration_ms=_action_duration_ms(content),
            )
        )
        planned.append(
            PlannedSegment(
                kind="pause",
                text="",
                planned_duration_ms=pause_after_dialogue_ms,
            )
        )

    has_meaningful = any(
        (
            (seg.kind in {"dialogue", "action"} and seg.text.strip())
            or (seg.kind == "pause" and seg.text.strip())
        )
        for seg in planned
    )
    if not has_meaningful:
        planned = [
            PlannedSegment(
                kind="action",
                text="(no_dialogue)",
                timing="mid",
                planned_duration_ms=2000,
            )
        ]

    return planned
