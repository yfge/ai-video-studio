"""Choose a stable storyboard grid size from structured clip motion beats."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .grid_storyboard_layout import grid_layout
from .grid_storyboard_prompt_layers import normalize_motion_timeline


@dataclass(frozen=True, slots=True)
class ClipStoryboardPanelSelection:
    panel_count: int
    mode: str
    visual_beat_count: int
    duration_ms: int
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def select_clip_storyboard_panel_count(
    clip: Mapping[str, Any],
    requested_panel_count: int | None,
) -> ClipStoryboardPanelSelection:
    """Use an explicit count or map LLM-authored motion beats to 2/4/6/9."""

    duration_ms = _duration_ms(clip)
    beats = _visual_beats(clip)
    if requested_panel_count is not None:
        count = grid_layout(requested_panel_count).panel_count
        return ClipStoryboardPanelSelection(
            panel_count=count,
            mode="fixed",
            visual_beat_count=len(beats),
            duration_ms=duration_ms,
            reason="operator_requested_panel_count",
        )

    count, reason = _automatic_count(len(beats), duration_ms)
    return ClipStoryboardPanelSelection(
        panel_count=count,
        mode="auto",
        visual_beat_count=len(beats),
        duration_ms=duration_ms,
        reason=reason,
    )


def _automatic_count(beat_count: int, duration_ms: int) -> tuple[int, str]:
    duration_cap = _duration_panel_cap(duration_ms)
    if beat_count:
        beat_count_target = _beat_panel_target(beat_count, duration_ms)
        return min(beat_count_target, duration_cap), "structured_visual_beats"
    return duration_cap, "duration_fallback_no_structured_beats"


def _beat_panel_target(beat_count: int, duration_ms: int) -> int:
    if beat_count <= 2:
        return 2
    if beat_count <= 4:
        return 4
    if beat_count <= 6 or duration_ms <= 16000:
        return 6
    return 9


def _duration_panel_cap(duration_ms: int) -> int:
    if duration_ms <= 4000:
        return 2
    if duration_ms <= 10000:
        return 4
    if duration_ms <= 16000:
        return 6
    return 9


def _visual_beats(clip: Mapping[str, Any]) -> list[dict[str, Any]]:
    source_refs = clip.get("source_refs")
    shot_plan = (
        source_refs.get("timeline_shot_plan")
        if isinstance(source_refs, Mapping)
        else None
    )
    raw_motion = (
        shot_plan.get("motion_timeline")
        if isinstance(shot_plan, Mapping)
        else clip.get("motion_timeline")
    )
    beats = normalize_motion_timeline(raw_motion)
    distinct: list[dict[str, Any]] = []
    for beat in beats:
        action_key = " ".join(str(beat.get("action") or "").lower().split())
        if not action_key or any(item["action_key"] == action_key for item in distinct):
            continue
        distinct.append({**beat, "action_key": action_key})
    return distinct


def _duration_ms(clip: Mapping[str, Any]) -> int:
    try:
        start_ms = int(clip.get("start_ms"))
        end_ms = int(clip.get("end_ms"))
        if end_ms > start_ms:
            return end_ms - start_ms
    except (TypeError, ValueError):
        pass
    try:
        return max(0, int(clip.get("duration_ms") or 0))
    except (TypeError, ValueError):
        return 0
