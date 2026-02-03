"""Concrete Context Specifications for Agents.

Defines specific context structures for different agent types:
- StoryContext: For story generation
- EpisodeContext: For episode generation
- ScriptContext: For script generation
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.services.agent_core.context_spec import (
    ContextSpec,
    FieldPriority,
    FieldSpec,
    TruncationStrategy,
    is_non_empty_list,
    is_non_empty_string,
    is_positive_int,
    normalize_newlines,
    strip_whitespace,
)


class StoryContext(ContextSpec):
    """Context specification for Story Agent."""

    FIELDS = [
        FieldSpec(
            name="title",
            description="Story title",
            priority=FieldPriority.CRITICAL,
            required=True,
            validator=is_non_empty_string,
            transformer=strip_whitespace,
        ),
        FieldSpec(
            name="genre",
            description="Story genre (e.g., 悬疑, 都市, 古装)",
            priority=FieldPriority.HIGH,
            required=True,
            validator=is_non_empty_string,
        ),
        FieldSpec(
            name="target_duration",
            description="Target total duration in seconds",
            priority=FieldPriority.HIGH,
            validator=is_positive_int,
        ),
        FieldSpec(
            name="episode_count",
            description="Number of episodes",
            priority=FieldPriority.HIGH,
            validator=is_positive_int,
        ),
        FieldSpec(
            name="characters",
            description="Character definitions",
            priority=FieldPriority.CRITICAL,
            max_tokens=1000,
            truncation=TruncationStrategy.NONE,
            validator=is_non_empty_list,
        ),
        FieldSpec(
            name="setting",
            description="World setting and background",
            priority=FieldPriority.HIGH,
            max_tokens=500,
            truncation=TruncationStrategy.TAIL,
        ),
        FieldSpec(
            name="theme",
            description="Central theme or message",
            priority=FieldPriority.MEDIUM,
            max_tokens=200,
        ),
        FieldSpec(
            name="tone",
            description="Story tone (e.g., 轻松, 紧张, 温馨)",
            priority=FieldPriority.MEDIUM,
        ),
        FieldSpec(
            name="constraints",
            description="Content constraints and restrictions",
            priority=FieldPriority.HIGH,
            max_tokens=300,
        ),
        FieldSpec(
            name="hook_requirements",
            description="Hook and cliffhanger requirements",
            priority=FieldPriority.MEDIUM,
            max_tokens=300,
        ),
    ]


class EpisodeContext(ContextSpec):
    """Context specification for Episode Agent."""

    FIELDS = [
        FieldSpec(
            name="story_outline",
            description="Overall story outline",
            priority=FieldPriority.CRITICAL,
            required=True,
            max_tokens=1500,
            truncation=TruncationStrategy.TAIL,
        ),
        FieldSpec(
            name="episode_number",
            description="Current episode number",
            priority=FieldPriority.CRITICAL,
            required=True,
            validator=is_positive_int,
        ),
        FieldSpec(
            name="total_episodes",
            description="Total number of episodes",
            priority=FieldPriority.HIGH,
            validator=is_positive_int,
        ),
        FieldSpec(
            name="target_duration",
            description="Target episode duration in seconds",
            priority=FieldPriority.HIGH,
            validator=is_positive_int,
        ),
        FieldSpec(
            name="characters",
            description="Character list with current states",
            priority=FieldPriority.CRITICAL,
            max_tokens=800,
            truncation=TruncationStrategy.NONE,
        ),
        FieldSpec(
            name="continuity_ledger",
            description="Continuity information from previous episodes",
            priority=FieldPriority.HIGH,
            max_tokens=1000,
            truncation=TruncationStrategy.TAIL,
        ),
        FieldSpec(
            name="previous_summary",
            description="Summary of previous episode",
            priority=FieldPriority.MEDIUM,
            max_tokens=500,
        ),
        FieldSpec(
            name="arc_requirements",
            description="Character arc requirements for this episode",
            priority=FieldPriority.MEDIUM,
            max_tokens=400,
        ),
        FieldSpec(
            name="hook_plan",
            description="Hook and cliffhanger plan for this episode",
            priority=FieldPriority.MEDIUM,
            max_tokens=200,
        ),
    ]


class ScriptContext(ContextSpec):
    """Context specification for Script Agent."""

    FIELDS = [
        FieldSpec(
            name="episode_outline",
            description="Episode outline to expand",
            priority=FieldPriority.CRITICAL,
            required=True,
            max_tokens=1000,
            truncation=TruncationStrategy.TAIL,
        ),
        FieldSpec(
            name="scene_index",
            description="Current scene index (0-based)",
            priority=FieldPriority.CRITICAL,
            required=True,
        ),
        FieldSpec(
            name="scene_info",
            description="Scene setup information",
            priority=FieldPriority.CRITICAL,
            max_tokens=500,
        ),
        FieldSpec(
            name="characters_in_scene",
            description="Characters present in scene",
            priority=FieldPriority.CRITICAL,
            max_tokens=600,
            truncation=TruncationStrategy.NONE,
        ),
        FieldSpec(
            name="dialogue_style",
            description="Dialogue style requirements",
            priority=FieldPriority.HIGH,
            max_tokens=300,
        ),
        FieldSpec(
            name="target_word_count",
            description="Target word count for scene",
            priority=FieldPriority.HIGH,
            validator=is_positive_int,
        ),
        FieldSpec(
            name="emotional_arc",
            description="Emotional arc for the scene",
            priority=FieldPriority.MEDIUM,
            max_tokens=200,
        ),
        FieldSpec(
            name="continuity_context",
            description="Relevant continuity information",
            priority=FieldPriority.MEDIUM,
            max_tokens=400,
            truncation=TruncationStrategy.TAIL,
        ),
        FieldSpec(
            name="previous_scene_summary",
            description="Summary of previous scene",
            priority=FieldPriority.LOW,
            max_tokens=200,
        ),
    ]


class TimelineContext(ContextSpec):
    """Context specification for Timeline Agent."""

    FIELDS = [
        FieldSpec(
            name="script",
            description="Full script to timeline",
            priority=FieldPriority.CRITICAL,
            required=True,
            max_tokens=3000,
            truncation=TruncationStrategy.NONE,
        ),
        FieldSpec(
            name="target_duration",
            description="Target total duration in seconds",
            priority=FieldPriority.CRITICAL,
            required=True,
            validator=is_positive_int,
        ),
        FieldSpec(
            name="wps_config",
            description="Words-per-second configuration",
            priority=FieldPriority.HIGH,
        ),
        FieldSpec(
            name="pause_rules",
            description="Pause duration rules",
            priority=FieldPriority.MEDIUM,
            max_tokens=200,
        ),
        FieldSpec(
            name="emotional_markers",
            description="Emotional markers requiring timing adjustment",
            priority=FieldPriority.MEDIUM,
            max_tokens=300,
        ),
    ]


class StoryboardContext(ContextSpec):
    """Context specification for Storyboard Agent."""

    FIELDS = [
        FieldSpec(
            name="script_beat",
            description="Script beat to visualize",
            priority=FieldPriority.CRITICAL,
            required=True,
            max_tokens=800,
        ),
        FieldSpec(
            name="characters",
            description="Characters with visual descriptions",
            priority=FieldPriority.CRITICAL,
            max_tokens=600,
            truncation=TruncationStrategy.NONE,
        ),
        FieldSpec(
            name="scene_setting",
            description="Scene setting description",
            priority=FieldPriority.HIGH,
            max_tokens=300,
        ),
        FieldSpec(
            name="previous_frame",
            description="Previous frame for continuity",
            priority=FieldPriority.MEDIUM,
            max_tokens=400,
        ),
        FieldSpec(
            name="shot_requirements",
            description="Required shot type and angle",
            priority=FieldPriority.HIGH,
            max_tokens=200,
        ),
        FieldSpec(
            name="mood",
            description="Scene mood and lighting",
            priority=FieldPriority.MEDIUM,
            max_tokens=150,
        ),
        FieldSpec(
            name="visual_style",
            description="Visual style guide",
            priority=FieldPriority.MEDIUM,
            max_tokens=200,
        ),
    ]
