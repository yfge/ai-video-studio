"""
Timeline Agent - Intelligent gap/pause calculation for dialogue audio.

This module provides agents for AI-reasoned timing based on emotional context,
narrative pacing, and scene dynamics.

Two implementations available:
- TimelineReactAgent: New ReactAgentBase implementation (recommended)
- TimelineLangGraphAgent: Legacy LangGraph implementation
"""

from __future__ import annotations

from .agent import TimelineLangGraphAgent
from .react_agent import TimelineReactAgent
from .schemas import (
    DialogueContext,
    SceneContext,
    TimelineAgentState,
    TimingDecision,
    TimingPlan,
)

__all__ = [
    # New ReactAgent implementation
    "TimelineReactAgent",
    # Legacy LangGraph implementation
    "TimelineLangGraphAgent",
    # Schemas
    "SceneContext",
    "DialogueContext",
    "TimingDecision",
    "TimingPlan",
    "TimelineAgentState",
]
