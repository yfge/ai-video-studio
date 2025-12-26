"""Builders for planned scene audio segments."""

from __future__ import annotations

from typing import Any, Sequence

from .segment_models import PlannedSegment
from .text_utils import looks_like_silence


def plan_scene_segments(
    *,
    dialogues: Sequence[dict[str, Any]],
    stage_directions: Sequence[dict[str, Any]],
    pause_after_dialogue_ms: int = 300,
    action_base_ms: int = 800,
    action_per_char_ms: int = 20,
    action_max_ms: int = 3000,
) -> list[PlannedSegment]:
    """Build an ordered segment plan for a scene using fixed gaps."""

    return _build_segments_with_timing(
        dialogues=dialogues,
        stage_directions=stage_directions,
        timing_map={},
        pause_after_dialogue_ms=pause_after_dialogue_ms,
        action_base_ms=action_base_ms,
        action_per_char_ms=action_per_char_ms,
        action_max_ms=action_max_ms,
    )


def _build_segments_with_timing(
    *,
    dialogues: Sequence[dict[str, Any]],
    stage_directions: Sequence[dict[str, Any]],
    timing_map: dict[int, int],
    pause_after_dialogue_ms: int = 300,
    action_base_ms: int = 800,
    action_per_char_ms: int = 20,
    action_max_ms: int = 3000,
) -> list[PlannedSegment]:
    """Build segments with custom timing from timing_map."""

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

    for idx, dlg in enumerate(dialogues):
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

        pause_duration = timing_map.get(idx, pause_after_dialogue_ms)
        if pause_duration > 0:
            planned.append(
                PlannedSegment(
                    kind="pause",
                    text="",
                    planned_duration_ms=pause_duration,
                )
            )

        if not mid_inserted and idx == 0 and stages_mid:
            for sd_content in stages_mid:
                planned.append(
                    PlannedSegment(
                        kind="action",
                        text=sd_content,
                        timing="mid",
                        planned_duration_ms=_action_duration_ms(sd_content),
                    )
                )
            mid_inserted = True

    if not mid_inserted and stages_mid:
        for content in stages_mid:
            planned.append(
                PlannedSegment(
                    kind="action",
                    text=content,
                    timing="mid",
                    planned_duration_ms=_action_duration_ms(content),
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

    return planned

