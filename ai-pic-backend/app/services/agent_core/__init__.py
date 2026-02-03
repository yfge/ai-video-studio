"""Core agent framework for AI generation pipelines.

This module provides base classes and utilities for building
robust AI agents with standardized error handling, repair loops,
and validation patterns.
"""

from app.services.agent_core.react_agent_base import (
    AgentError,
    AgentErrorType,
    AgentResult,
    AgentState,
    ReactAgentBase,
    RepairStrategy,
)
from app.services.agent_core.failure_patterns import (
    FailurePattern,
    FailurePatternMatcher,
    PatternCategory,
)

__all__ = [
    "AgentError",
    "AgentErrorType",
    "AgentResult",
    "AgentState",
    "FailurePattern",
    "FailurePatternMatcher",
    "PatternCategory",
    "ReactAgentBase",
    "RepairStrategy",
]
