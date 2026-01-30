"""Dialogue processing utilities (backwards-compatible facade)."""

from __future__ import annotations

from .dialogue_processing.scene_extractors import (
    extract_dialogues_for_scene,
    extract_scene_number,
    extract_stage_for_scene,
)
from .dialogue_processing.segment_builder import plan_scene_segments
from .dialogue_processing.segment_intelligent_planner import (
    plan_scene_segments_intelligent,
)
from .dialogue_processing.segment_models import PlannedSegment
from .dialogue_processing.text_utils import (
    looks_like_silence,
    norm_name,
    sanitize_dialogue_content,
)

__all__ = [
    "PlannedSegment",
    "norm_name",
    "looks_like_silence",
    "sanitize_dialogue_content",
    "extract_scene_number",
    "extract_dialogues_for_scene",
    "extract_stage_for_scene",
    "plan_scene_segments",
    "plan_scene_segments_intelligent",
]
