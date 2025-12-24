"""
Timeline Agent - Intelligent gap/pause calculation for dialogue audio.

This module provides a LangGraph-based agent that replaces fixed-interval
pause calculation with AI-reasoned timing based on emotional context,
narrative pacing, and scene dynamics.
"""

from __future__ import annotations

from .agent import TimelineLangGraphAgent
from .schemas import (
    DialogueContext,
    SceneContext,
    TimingDecision,
    TimingPlan,
    TimelineAgentState,
)

__all__ = [
    "TimelineLangGraphAgent",
    "SceneContext",
    "DialogueContext",
    "TimingDecision",
    "TimingPlan",
    "TimelineAgentState",
]
