"""ReAct Agent Base Class.

Provides a standardized base class for building AI agents with:
- Structured error handling (SYNTAX/SEMANTIC/BUDGET)
- Configurable repair strategies
- Validation hooks
- State management
- Logging and metrics
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from app.utils.json_utils import extract_json_block

logger = logging.getLogger(__name__)


class AgentErrorType(str, Enum):
    """Classification of agent errors for repair strategy selection."""

    SYNTAX = "syntax"  # JSON parsing, schema validation
    SEMANTIC = "semantic"  # Logic errors, content issues
    BUDGET = "budget"  # Token limits, timeout
    NETWORK = "network"  # API failures, connectivity
    VALIDATION = "validation"  # Business rule violations
    UNKNOWN = "unknown"


class RepairStrategy(str, Enum):
    """Strategies for repairing failed generations."""

    RETRY = "retry"  # Simple retry with same prompt
    REFINE = "refine"  # Retry with error feedback
    SIMPLIFY = "simplify"  # Reduce complexity/scope
    DECOMPOSE = "decompose"  # Break into smaller tasks
    FALLBACK = "fallback"  # Use default/cached result
    ABORT = "abort"  # Give up


@dataclass
class AgentError:
    """Structured error information for agent failures."""

    error_type: AgentErrorType
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    recoverable: bool = True
    suggested_strategy: RepairStrategy = RepairStrategy.RETRY

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "recoverable": self.recoverable,
            "suggested_strategy": self.suggested_strategy.value,
        }


@dataclass
class AgentState:
    """State tracking for agent execution."""

    attempt: int = 0
    max_attempts: int = 3
    errors: List[AgentError] = field(default_factory=list)
    intermediate_results: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    @property
    def has_remaining_attempts(self) -> bool:
        """Check if more attempts are available."""
        return self.attempt < self.max_attempts

    @property
    def duration_seconds(self) -> float:
        """Get execution duration in seconds."""
        end = self.completed_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()

    def add_error(self, error: AgentError) -> None:
        """Record an error."""
        self.errors.append(error)

    def add_intermediate(self, result: Dict[str, Any]) -> None:
        """Record an intermediate result."""
        self.intermediate_results.append(result)

    def complete(self) -> None:
        """Mark execution as complete."""
        self.completed_at = datetime.now(timezone.utc)


# Type variable for result type
T = TypeVar("T")


@dataclass
class AgentResult(Generic[T]):
    """Result container for agent execution."""

    success: bool
    data: Optional[T] = None
    errors: List[AgentError] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: T, metadata: Optional[Dict[str, Any]] = None) -> AgentResult[T]:
        """Create a successful result."""
        return cls(success=True, data=data, metadata=metadata or {})

    @classmethod
    def fail(
        cls, errors: List[AgentError], metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResult[T]:
        """Create a failed result."""
        return cls(success=False, errors=errors, metadata=metadata or {})

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "data": self.data,
            "errors": [e.to_dict() for e in self.errors],
            "metadata": self.metadata,
        }


class ReactAgentBase(ABC, Generic[T]):
    """Base class for ReAct-style agents with repair loops.

    Subclasses should implement:
    - _generate(): Core generation logic
    - _validate(): Validation of generated output
    - _repair(): Repair strategy implementation
    """

    def __init__(
        self,
        max_attempts: int = 3,
        repair_strategies: Optional[Dict[AgentErrorType, RepairStrategy]] = None,
    ):
        """Initialize the agent.

        Args:
            max_attempts: Maximum number of generation attempts
            repair_strategies: Mapping of error types to repair strategies
        """
        self.max_attempts = max_attempts
        self.repair_strategies = repair_strategies or self._default_repair_strategies()
        self._validators: List[Callable[[T], List[AgentError]]] = []

    def _default_repair_strategies(self) -> Dict[AgentErrorType, RepairStrategy]:
        """Get default repair strategies for each error type."""
        return {
            AgentErrorType.SYNTAX: RepairStrategy.REFINE,
            AgentErrorType.SEMANTIC: RepairStrategy.REFINE,
            AgentErrorType.BUDGET: RepairStrategy.SIMPLIFY,
            AgentErrorType.NETWORK: RepairStrategy.RETRY,
            AgentErrorType.VALIDATION: RepairStrategy.REFINE,
            AgentErrorType.UNKNOWN: RepairStrategy.RETRY,
        }

    def add_validator(self, validator: Callable[[T], List[AgentError]]) -> None:
        """Add a validation function to the pipeline.

        Args:
            validator: Function that takes result and returns list of errors
        """
        self._validators.append(validator)

    async def run(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResult[T]:
        """Execute the agent with repair loop.

        Args:
            input_data: Input data for generation
            context: Optional additional context

        Returns:
            AgentResult with success/failure and data/errors
        """
        state = AgentState(max_attempts=self.max_attempts, context=context or {})

        while state.has_remaining_attempts:
            state.attempt += 1
            logger.info(f"Agent attempt {state.attempt}/{state.max_attempts}")

            try:
                # Generate
                raw_result = await self._generate(input_data, state)

                # Parse if needed
                parsed = self._parse_result(raw_result)
                if parsed is None:
                    error = AgentError(
                        error_type=AgentErrorType.SYNTAX,
                        message="Failed to parse generation result",
                        details={"raw": str(raw_result)[:500]},
                    )
                    state.add_error(error)
                    input_data = self._apply_repair(input_data, error, state)
                    continue

                # Validate
                validation_errors = self._validate(parsed, state)

                # Run additional validators
                for validator in self._validators:
                    validation_errors.extend(validator(parsed))

                if validation_errors:
                    state.errors.extend(validation_errors)
                    recoverable = any(e.recoverable for e in validation_errors)
                    if not recoverable or not state.has_remaining_attempts:
                        state.complete()
                        return AgentResult.fail(
                            state.errors, {"attempts": state.attempt}
                        )
                    # Apply repair for first error
                    input_data = self._apply_repair(
                        input_data, validation_errors[0], state
                    )
                    continue

                # Success
                state.complete()
                return AgentResult.ok(
                    parsed,
                    {
                        "attempts": state.attempt,
                        "duration_seconds": state.duration_seconds,
                    },
                )

            except Exception as e:
                error = self._classify_error(e)
                state.add_error(error)
                logger.warning(f"Agent error: {error.message}", exc_info=True)

                if not error.recoverable or not state.has_remaining_attempts:
                    break

                input_data = self._apply_repair(input_data, error, state)

        state.complete()
        return AgentResult.fail(state.errors, {"attempts": state.attempt})

    @abstractmethod
    async def _generate(
        self, input_data: Dict[str, Any], state: AgentState
    ) -> Any:
        """Core generation logic. Must be implemented by subclasses.

        Args:
            input_data: Input data for generation
            state: Current agent state

        Returns:
            Raw generation result (may need parsing)
        """
        pass

    def _parse_result(self, raw_result: Any) -> Optional[T]:
        """Parse raw result into expected type.

        Override for custom parsing logic.

        Args:
            raw_result: Raw generation result

        Returns:
            Parsed result or None if parsing failed
        """
        if isinstance(raw_result, dict):
            return raw_result
        if isinstance(raw_result, str):
            return extract_json_block(raw_result)
        return None

    def _validate(self, result: T, state: AgentState) -> List[AgentError]:
        """Validate generation result.

        Override to add custom validation logic.

        Args:
            result: Parsed generation result
            state: Current agent state

        Returns:
            List of validation errors (empty if valid)
        """
        return []

    def _apply_repair(
        self,
        input_data: Dict[str, Any],
        error: AgentError,
        state: AgentState,
    ) -> Dict[str, Any]:
        """Apply repair strategy based on error type.

        Args:
            input_data: Current input data
            error: The error that triggered repair
            state: Current agent state

        Returns:
            Modified input data for retry
        """
        strategy = self.repair_strategies.get(
            error.error_type, RepairStrategy.RETRY
        )
        logger.info(f"Applying repair strategy: {strategy.value}")

        if strategy == RepairStrategy.REFINE:
            return self._refine_input(input_data, error, state)
        elif strategy == RepairStrategy.SIMPLIFY:
            return self._simplify_input(input_data, state)
        elif strategy == RepairStrategy.DECOMPOSE:
            return self._decompose_input(input_data, state)
        else:
            return input_data

    def _refine_input(
        self,
        input_data: Dict[str, Any],
        error: AgentError,
        state: AgentState,
    ) -> Dict[str, Any]:
        """Refine input with error feedback.

        Override for custom refinement logic.
        """
        refined = dict(input_data)
        refined["_error_feedback"] = error.message
        refined["_error_type"] = error.error_type.value
        return refined

    def _simplify_input(
        self,
        input_data: Dict[str, Any],
        state: AgentState,
    ) -> Dict[str, Any]:
        """Simplify input to reduce complexity.

        Override for custom simplification logic.
        """
        return input_data

    def _decompose_input(
        self,
        input_data: Dict[str, Any],
        state: AgentState,
    ) -> Dict[str, Any]:
        """Decompose input into smaller tasks.

        Override for custom decomposition logic.
        """
        return input_data

    def _classify_error(self, exception: Exception) -> AgentError:
        """Classify an exception into an AgentError.

        Args:
            exception: The exception to classify

        Returns:
            Classified AgentError
        """
        error_msg = str(exception)

        # JSON/Schema errors
        if any(
            kw in error_msg.lower()
            for kw in ["json", "parse", "decode", "schema", "validation"]
        ):
            return AgentError(
                error_type=AgentErrorType.SYNTAX,
                message=f"Syntax error: {error_msg}",
                recoverable=True,
            )

        # Budget/limit errors
        if any(
            kw in error_msg.lower()
            for kw in ["token", "limit", "quota", "timeout", "exceeded"]
        ):
            return AgentError(
                error_type=AgentErrorType.BUDGET,
                message=f"Budget exceeded: {error_msg}",
                recoverable=True,
                suggested_strategy=RepairStrategy.SIMPLIFY,
            )

        # Network errors
        if any(
            kw in error_msg.lower()
            for kw in ["connection", "network", "timeout", "refused", "unreachable"]
        ):
            return AgentError(
                error_type=AgentErrorType.NETWORK,
                message=f"Network error: {error_msg}",
                recoverable=True,
            )

        # Default to unknown
        return AgentError(
            error_type=AgentErrorType.UNKNOWN,
            message=f"Unknown error: {error_msg}",
            recoverable=True,
        )
