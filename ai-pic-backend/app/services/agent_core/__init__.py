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
from app.services.agent_core.context_spec import (
    ContextSpec,
    FieldPriority,
    FieldSpec,
    TruncationStrategy,
    estimate_tokens,
    truncate_text,
    is_non_empty_string,
    is_non_empty_list,
    is_positive_int,
    strip_whitespace,
    normalize_newlines,
)

__all__ = [
    # Agent base
    "AgentError",
    "AgentErrorType",
    "AgentResult",
    "AgentState",
    "ReactAgentBase",
    "RepairStrategy",
    # Failure patterns
    "FailurePattern",
    "FailurePatternMatcher",
    "PatternCategory",
    # Context spec
    "ContextSpec",
    "FieldPriority",
    "FieldSpec",
    "TruncationStrategy",
    "estimate_tokens",
    "truncate_text",
    "is_non_empty_string",
    "is_non_empty_list",
    "is_positive_int",
    "strip_whitespace",
    "normalize_newlines",
]
