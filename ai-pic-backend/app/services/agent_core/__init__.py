"""Core agent framework for AI generation pipelines.

This module provides base classes and utilities for building
robust AI agents with standardized error handling, repair loops,
and validation patterns.
"""

from app.services.agent_core.context_spec import (
    ContextSpec,
    FieldPriority,
    FieldSpec,
    TruncationStrategy,
    estimate_tokens,
    is_non_empty_list,
    is_non_empty_string,
    is_positive_int,
    normalize_newlines,
    strip_whitespace,
    truncate_text,
)
from app.services.agent_core.failure_patterns import (
    FailurePattern,
    FailurePatternMatcher,
    PatternCategory,
)
from app.services.agent_core.graph_helpers import (
    append_reasoning,
    end_on_error_router,
    has_state_error,
    reset_control_flags,
    route_on_error,
)
from app.services.agent_core.quality_loop import (
    DeterministicValidator,
    FailureMode,
    RepairAttempt,
    RepairMetrics,
    RepairMonitor,
    SemanticValidator,
    TwoLayerValidator,
    ValidationLayer,
    ValidationResult,
)
from app.services.agent_core.react_agent_base import (
    AgentError,
    AgentErrorType,
    AgentResult,
    AgentState,
    ReactAgentBase,
    RepairStrategy,
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
    # Graph helpers
    "append_reasoning",
    "end_on_error_router",
    "has_state_error",
    "reset_control_flags",
    "route_on_error",
    # Quality loop
    "DeterministicValidator",
    "FailureMode",
    "RepairAttempt",
    "RepairMetrics",
    "RepairMonitor",
    "SemanticValidator",
    "TwoLayerValidator",
    "ValidationLayer",
    "ValidationResult",
]
