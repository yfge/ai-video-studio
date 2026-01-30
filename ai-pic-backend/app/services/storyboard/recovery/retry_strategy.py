"""
Intelligent retry strategy for storyboard generation.

Provides configurable retry logic with exponential backoff,
error classification, and adaptive parameter adjustment.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)
from enum import Enum
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class ErrorCategory(str, Enum):
    """Categories of errors for retry decisions."""

    TRANSIENT = "transient"  # Network issues, rate limits
    VALIDATION = "validation"  # Data validation failures
    GENERATION = "generation"  # AI generation failures
    RESOURCE = "resource"  # Missing resources
    FATAL = "fatal"  # Unrecoverable errors


@dataclass
class RetryContext:
    """Context for a retry operation."""

    operation: str
    attempt: int = 0
    max_attempts: int = 3
    last_error: str | None = None
    error_category: ErrorCategory | None = None
    started_at: datetime = field(default_factory=_utcnow)
    attempts_history: list[dict[str, Any]] = field(default_factory=list)

    # Adaptive parameters
    temperature_adjustment: float = 0.0
    provider_override: str | None = None
    reduced_scope: bool = False

    def record_attempt(
        self,
        success: bool,
        error: str | None = None,
        duration_ms: int = 0,
    ) -> None:
        """Record an attempt."""
        self.attempt += 1
        self.attempts_history.append({
            "attempt": self.attempt,
            "success": success,
            "error": error,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if error:
            self.last_error = error

    def can_retry(self) -> bool:
        """Check if retry is allowed."""
        return self.attempt < self.max_attempts

    def get_delay_seconds(self) -> float:
        """Get delay before next retry with exponential backoff."""
        base_delay = 1.0
        max_delay = 30.0
        delay = min(base_delay * (2 ** self.attempt), max_delay)
        return delay


class RetryStrategy:
    """
    Intelligent retry strategy for storyboard operations.

    Features:
    - Error categorization for retry decisions
    - Exponential backoff with jitter
    - Adaptive parameter adjustment
    - Provider fallback
    """

    # Errors that should not be retried
    FATAL_PATTERNS = [
        "script_not_found",
        "episode_not_found",
        "invalid_script_id",
        "permission_denied",
        "authentication_failed",
    ]

    # Errors that indicate transient issues
    TRANSIENT_PATTERNS = [
        "rate_limit",
        "timeout",
        "connection",
        "503",
        "429",
        "temporary",
    ]

    # Errors that might benefit from parameter adjustment
    GENERATION_PATTERNS = [
        "generation_failed",
        "invalid_response",
        "parse_error",
        "empty_result",
        "model_error",
    ]

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

    def categorize_error(self, error: str | Exception) -> ErrorCategory:
        """Categorize an error to determine retry strategy."""
        error_str = str(error).lower()

        for pattern in self.FATAL_PATTERNS:
            if pattern in error_str:
                return ErrorCategory.FATAL

        for pattern in self.TRANSIENT_PATTERNS:
            if pattern in error_str:
                return ErrorCategory.TRANSIENT

        for pattern in self.GENERATION_PATTERNS:
            if pattern in error_str:
                return ErrorCategory.GENERATION

        if "validation" in error_str or "invalid" in error_str:
            return ErrorCategory.VALIDATION

        if "not_found" in error_str or "missing" in error_str:
            return ErrorCategory.RESOURCE

        return ErrorCategory.TRANSIENT  # Default to retryable

    def should_retry(
        self,
        context: RetryContext,
        error: str | Exception,
    ) -> bool:
        """Determine if operation should be retried."""
        if not context.can_retry():
            return False

        category = self.categorize_error(error)
        context.error_category = category

        if category == ErrorCategory.FATAL:
            return False

        if category == ErrorCategory.RESOURCE:
            return False  # Missing resources won't appear on retry

        return True

    def adjust_parameters(
        self,
        context: RetryContext,
        current_params: dict[str, Any],
    ) -> dict[str, Any]:
        """Adjust parameters for retry based on error pattern."""
        adjusted = dict(current_params)

        category = context.error_category

        if category == ErrorCategory.GENERATION:
            # Lower temperature for more deterministic output
            current_temp = adjusted.get("temperature", 0.7)
            adjusted["temperature"] = max(0.1, current_temp - 0.2)
            context.temperature_adjustment = adjusted["temperature"] - current_temp

        if category == ErrorCategory.TRANSIENT:
            # Could switch provider on repeated transient failures
            if context.attempt >= 2:
                # Signal that provider switch might help
                context.provider_override = "fallback"

        return adjusted

    async def execute_with_retry(
        self,
        operation: str,
        func: Callable[..., T],
        *args: Any,
        max_attempts: int | None = None,
        **kwargs: Any,
    ) -> tuple[T | None, RetryContext]:
        """
        Execute a function with retry logic.

        Args:
            operation: Name of operation for logging
            func: Async function to execute
            *args: Positional arguments for func
            max_attempts: Override default max attempts
            **kwargs: Keyword arguments for func

        Returns:
            Tuple of (result, retry_context)
        """
        context = RetryContext(
            operation=operation,
            max_attempts=max_attempts or self.max_attempts,
        )

        while True:
            start = datetime.now(timezone.utc)
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                duration = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
                context.record_attempt(success=True, duration_ms=duration)
                return result, context

            except Exception as e:
                duration = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
                error_str = str(e)
                context.record_attempt(
                    success=False, error=error_str, duration_ms=duration
                )

                if not self.should_retry(context, e):
                    return None, context

                # Adjust parameters for next attempt
                kwargs = self.adjust_parameters(context, kwargs)

                # Wait before retry
                delay = context.get_delay_seconds()
                await asyncio.sleep(delay)

    def create_context(self, operation: str) -> RetryContext:
        """Create a new retry context."""
        return RetryContext(
            operation=operation,
            max_attempts=self.max_attempts,
        )
