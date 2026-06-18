"""Fallback panel moment profiles for one-clip storyboard sheets."""

from __future__ import annotations

from typing import Any, Dict, Mapping

_PROFILES = (
    {
        "label": "Opening frame",
        "shot_type": "wide establishing shot",
        "composition": "wide composition that establishes the space and character positions",
        "motion": "establish the location, blocking, and starting posture",
        "landing": "clear spatial orientation",
    },
    {
        "label": "Interaction frame",
        "shot_type": "medium two-shot",
        "composition": "medium composition centered on character body language and shared eyelines",
        "motion": "show the main interaction or intent inside the beat",
        "landing": "relationship tension is readable",
    },
    {
        "label": "Detail frame",
        "shot_type": "insert detail shot",
        "composition": "tighter composition on the most relevant prop, gesture, or environmental detail",
        "motion": "isolate the concrete visual detail that makes the beat specific",
        "landing": "the action detail is unambiguous",
    },
    {
        "label": "Reaction frame",
        "shot_type": "reaction close-up",
        "composition": "close composition on facial reaction or posture change",
        "motion": "capture the emotional response to the preceding action",
        "landing": "the emotional turn is clear",
    },
    {
        "label": "Shift frame",
        "shot_type": "over-the-shoulder shot",
        "composition": "over-the-shoulder composition that changes perspective while preserving continuity",
        "motion": "show a viewpoint shift within the same beat",
        "landing": "the scene gains a new point of view",
    },
    {
        "label": "Movement frame",
        "shot_type": "dynamic medium shot",
        "composition": "dynamic composition with foreground and background separation",
        "motion": "show the beat progressing through a clear physical movement",
        "landing": "the action feels in progress",
    },
    {
        "label": "Pressure frame",
        "shot_type": "tight two-shot",
        "composition": "compressed composition that increases dramatic pressure between subjects",
        "motion": "tighten the blocking to emphasize conflict or urgency",
        "landing": "pressure is visually heightened",
    },
    {
        "label": "Decision frame",
        "shot_type": "clean close-up",
        "composition": "clean close-up that isolates the deciding expression or gesture",
        "motion": "show the moment of choice or realization",
        "landing": "the decision beat is readable",
    },
    {
        "label": "Closing frame",
        "shot_type": "held closing shot",
        "composition": "held composition that resolves the beat and preserves screen direction",
        "motion": "hold the final posture or reaction as the beat lands",
        "landing": "a clear final visual beat",
    },
)

_FOUR_PANEL_PROFILE_INDEXES = (0, 1, 2, 8)


def clip_panel_fallback_layers(
    clip: Mapping[str, Any],
    *,
    panel_index: int,
    panel_count: int,
) -> Dict[str, Any]:
    profile = _profile(panel_index, panel_count)
    at_ms = _panel_anchor_ms(clip, panel_index, panel_count)
    moment = f"{profile['label']}: {profile['motion']}"
    return {
        "panel_moment": moment,
        "shot_type": profile["shot_type"],
        "camera_movement": "stable continuity camera",
        "composition_geometry": profile["composition"],
        "motion_timeline": [{"at_ms": at_ms, "action": profile["motion"]}],
        "emotional_landing": profile["landing"],
    }


def _profile(panel_index: int, panel_count: int) -> Mapping[str, str]:
    if panel_count == 4:
        profile_index = _FOUR_PANEL_PROFILE_INDEXES[panel_index - 1]
    elif panel_count <= len(_PROFILES):
        profile_index = panel_index - 1
    else:
        ratio = (panel_index - 1) / max(1, panel_count - 1)
        profile_index = round(ratio * (len(_PROFILES) - 1))
    return _PROFILES[profile_index]


def _panel_anchor_ms(
    clip: Mapping[str, Any],
    panel_index: int,
    panel_count: int,
) -> int:
    start_ms = clip.get("start_ms")
    end_ms = clip.get("end_ms")
    if isinstance(start_ms, (int, float)) and isinstance(end_ms, (int, float)):
        duration = max(0, int(end_ms - start_ms))
        if panel_count <= 1:
            return int(start_ms)
        return int(start_ms) + round(duration * (panel_index - 1) / panel_count)
    return 0
