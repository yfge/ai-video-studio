"""Quality Closed Loop System.

Provides two-layer validation, failure mode recognition,
and repair success rate monitoring for agent pipelines.

Key features:
- Fast deterministic validation (JSON, schema, rules)
- Deep LLM-based semantic validation
- Failure pattern classification
- Repair success rate tracking with SLO alerts
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from app.services.agent_core.failure_patterns import (
    FailurePatternMatcher,
    PatternCategory,
)

logger = logging.getLogger(__name__)


class ValidationLayer(str, Enum):
    """Validation layer types."""

    DETERMINISTIC = "deterministic"  # Fast, rule-based
    SEMANTIC = "semantic"  # Deep, LLM-based


class FailureMode(str, Enum):
    """Recognized failure modes for classification."""

    JSON_PARSE = "json_parse"
    SCHEMA_VIOLATION = "schema_violation"
    CONTENT_CONSTRAINT = "content_constraint"
    LOGIC_ERROR = "logic_error"
    CHARACTER_INCONSISTENCY = "character_inconsistency"
    TIMELINE_ERROR = "timeline_error"
    API_ERROR = "api_error"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Result from a validation check."""

    passed: bool
    layer: ValidationLayer
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    failure_mode: Optional[FailureMode] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "passed": self.passed,
            "layer": self.layer.value,
            "errors": self.errors,
            "warnings": self.warnings,
            "failure_mode": self.failure_mode.value if self.failure_mode else None,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


T = TypeVar("T")


class DeterministicValidator(Generic[T]):
    """Fast, rule-based validator.

    Performs quick checks that don't require LLM:
    - JSON syntax validation
    - Schema compliance
    - Business rules
    - Content constraints
    """

    def __init__(self):
        """Initialize validator with rule registry."""
        self._rules: List[Callable[[T], List[str]]] = []
        self._pattern_matcher = FailurePatternMatcher()

    def add_rule(self, rule: Callable[[T], List[str]]) -> None:
        """Add a validation rule.

        Args:
            rule: Function that takes data and returns list of error messages
        """
        self._rules.append(rule)

    def validate(self, data: T) -> ValidationResult:
        """Run all validation rules.

        Args:
            data: Data to validate

        Returns:
            ValidationResult with pass/fail and errors
        """
        start = time.time()
        all_errors = []

        for rule in self._rules:
            try:
                errors = rule(data)
                all_errors.extend(errors)
            except Exception as e:
                all_errors.append(f"Rule execution error: {str(e)}")

        duration_ms = (time.time() - start) * 1000

        failure_mode = None
        if all_errors:
            failure_mode = self._classify_failure_mode(all_errors)

        return ValidationResult(
            passed=len(all_errors) == 0,
            layer=ValidationLayer.DETERMINISTIC,
            errors=all_errors,
            failure_mode=failure_mode,
            duration_ms=duration_ms,
        )

    def _classify_failure_mode(self, errors: List[str]) -> FailureMode:
        """Classify errors into failure mode.

        Args:
            errors: List of error messages

        Returns:
            Classified failure mode
        """
        error_text = " ".join(errors).lower()

        # Use pattern matcher for classification
        for error in errors:
            category = self._pattern_matcher.classify_category(error)
            if category:
                return self._category_to_mode(category)

        # Fallback heuristics
        if any(kw in error_text for kw in ["json", "parse", "syntax", "decode"]):
            return FailureMode.JSON_PARSE
        if any(kw in error_text for kw in ["schema", "type", "required", "field"]):
            return FailureMode.SCHEMA_VIOLATION
        if any(kw in error_text for kw in ["character", "角色", "人物"]):
            return FailureMode.CHARACTER_INCONSISTENCY
        if any(kw in error_text for kw in ["timeline", "时间", "顺序"]):
            return FailureMode.TIMELINE_ERROR
        if any(kw in error_text for kw in ["api", "rate", "limit", "timeout"]):
            return FailureMode.API_ERROR

        return FailureMode.UNKNOWN

    def _category_to_mode(self, category: PatternCategory) -> FailureMode:
        """Map pattern category to failure mode."""
        mapping = {
            PatternCategory.JSON_SYNTAX: FailureMode.JSON_PARSE,
            PatternCategory.SCHEMA_VIOLATION: FailureMode.SCHEMA_VIOLATION,
            PatternCategory.MISSING_FIELD: FailureMode.SCHEMA_VIOLATION,
            PatternCategory.CONTENT_LENGTH: FailureMode.CONTENT_CONSTRAINT,
            PatternCategory.CHARACTER_INCONSISTENCY: FailureMode.CHARACTER_INCONSISTENCY,
            PatternCategory.TIMELINE_ERROR: FailureMode.TIMELINE_ERROR,
            PatternCategory.LOGIC_ERROR: FailureMode.LOGIC_ERROR,
            PatternCategory.FORMAT_ERROR: FailureMode.SCHEMA_VIOLATION,
            PatternCategory.API_ERROR: FailureMode.API_ERROR,
        }
        return mapping.get(category, FailureMode.UNKNOWN)


class SemanticValidator(Generic[T]):
    """Deep, LLM-based semantic validator.

    Performs deeper analysis that requires understanding:
    - Narrative coherence
    - Character behavior consistency
    - Dialogue quality
    - Emotional arc validity
    """

    def __init__(self, llm_callable: Optional[Callable[[str], str]] = None):
        """Initialize with optional LLM callable.

        Args:
            llm_callable: Function to call LLM for semantic validation
        """
        self._llm = llm_callable
        self._checks: List[Callable[[T], List[str]]] = []

    def add_check(self, check: Callable[[T], List[str]]) -> None:
        """Add a semantic check.

        Args:
            check: Function that performs semantic validation
        """
        self._checks.append(check)

    def validate(self, data: T) -> ValidationResult:
        """Run semantic validation.

        Args:
            data: Data to validate

        Returns:
            ValidationResult with pass/fail and errors
        """
        start = time.time()
        all_errors = []
        all_warnings = []

        for check in self._checks:
            try:
                errors = check(data)
                all_errors.extend(errors)
            except Exception as e:
                all_warnings.append(f"Semantic check error: {str(e)}")

        duration_ms = (time.time() - start) * 1000

        failure_mode = None
        if all_errors:
            failure_mode = FailureMode.LOGIC_ERROR

        return ValidationResult(
            passed=len(all_errors) == 0,
            layer=ValidationLayer.SEMANTIC,
            errors=all_errors,
            warnings=all_warnings,
            failure_mode=failure_mode,
            duration_ms=duration_ms,
        )


class TwoLayerValidator(Generic[T]):
    """Two-layer validation pipeline.

    Runs fast deterministic validation first, then semantic
    validation only if deterministic passes (for efficiency).
    """

    def __init__(
        self,
        deterministic: DeterministicValidator[T],
        semantic: Optional[SemanticValidator[T]] = None,
        skip_semantic_on_fast_fail: bool = True,
    ):
        """Initialize with validators.

        Args:
            deterministic: Fast rule-based validator
            semantic: Deep semantic validator (optional)
            skip_semantic_on_fast_fail: Skip semantic if deterministic fails
        """
        self.deterministic = deterministic
        self.semantic = semantic
        self.skip_semantic_on_fast_fail = skip_semantic_on_fast_fail

    def validate(self, data: T) -> List[ValidationResult]:
        """Run two-layer validation.

        Args:
            data: Data to validate

        Returns:
            List of ValidationResults (one per layer executed)
        """
        results = []

        # Layer 1: Deterministic
        det_result = self.deterministic.validate(data)
        results.append(det_result)

        # Layer 2: Semantic (conditional)
        if self.semantic:
            if det_result.passed or not self.skip_semantic_on_fast_fail:
                sem_result = self.semantic.validate(data)
                results.append(sem_result)

        return results

    def is_valid(self, data: T) -> bool:
        """Quick check if data passes all layers.

        Args:
            data: Data to validate

        Returns:
            True if all layers pass
        """
        results = self.validate(data)
        return all(r.passed for r in results)


@dataclass
class RepairAttempt:
    """Record of a repair attempt."""

    timestamp: datetime
    failure_mode: FailureMode
    repair_strategy: str
    success: bool
    duration_ms: float
    error_before: str
    error_after: Optional[str] = None


@dataclass
class RepairMetrics:
    """Aggregated repair success metrics."""

    total_attempts: int = 0
    successful_repairs: int = 0
    by_failure_mode: Dict[FailureMode, Dict[str, int]] = field(
        default_factory=lambda: {}
    )
    by_strategy: Dict[str, Dict[str, int]] = field(default_factory=lambda: {})
    avg_duration_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_attempts == 0:
            return 0.0
        return self.successful_repairs / self.total_attempts

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "total_attempts": self.total_attempts,
            "successful_repairs": self.successful_repairs,
            "success_rate": self.success_rate,
            "by_failure_mode": {
                k.value: v for k, v in self.by_failure_mode.items()
            },
            "by_strategy": self.by_strategy,
            "avg_duration_ms": self.avg_duration_ms,
        }


class RepairMonitor:
    """Monitors repair success rates with SLO alerting.

    Tracks repair attempts and their outcomes to:
    - Calculate success rates by failure mode and strategy
    - Alert when SLO thresholds are breached
    - Identify problematic patterns
    """

    def __init__(
        self,
        slo_threshold: float = 0.7,
        window_size: int = 100,
        alert_callback: Optional[Callable[[str, Dict], None]] = None,
    ):
        """Initialize monitor.

        Args:
            slo_threshold: Minimum acceptable success rate (0-1)
            window_size: Number of recent attempts to consider
            alert_callback: Function to call when SLO breached
        """
        self.slo_threshold = slo_threshold
        self.window_size = window_size
        self.alert_callback = alert_callback
        self._attempts: List[RepairAttempt] = []
        self._alerts_sent: Dict[str, datetime] = {}
        self._alert_cooldown = timedelta(minutes=5)

    def record_attempt(self, attempt: RepairAttempt) -> None:
        """Record a repair attempt.

        Args:
            attempt: The repair attempt to record
        """
        self._attempts.append(attempt)

        # Trim to window size
        if len(self._attempts) > self.window_size * 2:
            self._attempts = self._attempts[-self.window_size:]

        # Check SLO
        self._check_slo(attempt.failure_mode)

    def record(
        self,
        failure_mode: FailureMode,
        strategy: str,
        success: bool,
        duration_ms: float,
        error_before: str,
        error_after: Optional[str] = None,
    ) -> None:
        """Convenience method to record attempt.

        Args:
            failure_mode: Type of failure being repaired
            strategy: Repair strategy used
            success: Whether repair succeeded
            duration_ms: Time taken for repair
            error_before: Original error message
            error_after: Error after repair (if still failing)
        """
        attempt = RepairAttempt(
            timestamp=datetime.now(timezone.utc),
            failure_mode=failure_mode,
            repair_strategy=strategy,
            success=success,
            duration_ms=duration_ms,
            error_before=error_before,
            error_after=error_after,
        )
        self.record_attempt(attempt)

    def get_metrics(self, window: Optional[int] = None) -> RepairMetrics:
        """Calculate repair metrics over recent window.

        Args:
            window: Number of attempts to consider (default: all)

        Returns:
            Aggregated RepairMetrics
        """
        attempts = self._attempts[-(window or len(self._attempts)):]

        if not attempts:
            return RepairMetrics()

        metrics = RepairMetrics(
            total_attempts=len(attempts),
            successful_repairs=sum(1 for a in attempts if a.success),
        )

        # By failure mode
        for mode in FailureMode:
            mode_attempts = [a for a in attempts if a.failure_mode == mode]
            if mode_attempts:
                metrics.by_failure_mode[mode] = {
                    "total": len(mode_attempts),
                    "success": sum(1 for a in mode_attempts if a.success),
                }

        # By strategy
        strategies = set(a.repair_strategy for a in attempts)
        for strategy in strategies:
            strat_attempts = [a for a in attempts if a.repair_strategy == strategy]
            metrics.by_strategy[strategy] = {
                "total": len(strat_attempts),
                "success": sum(1 for a in strat_attempts if a.success),
            }

        # Average duration
        if attempts:
            metrics.avg_duration_ms = sum(a.duration_ms for a in attempts) / len(attempts)

        return metrics

    def get_success_rate(
        self,
        failure_mode: Optional[FailureMode] = None,
        strategy: Optional[str] = None,
    ) -> float:
        """Get success rate with optional filtering.

        Args:
            failure_mode: Filter by failure mode
            strategy: Filter by strategy

        Returns:
            Success rate (0-1)
        """
        attempts = self._attempts[-self.window_size:]

        if failure_mode:
            attempts = [a for a in attempts if a.failure_mode == failure_mode]
        if strategy:
            attempts = [a for a in attempts if a.repair_strategy == strategy]

        if not attempts:
            return 0.0

        return sum(1 for a in attempts if a.success) / len(attempts)

    def _check_slo(self, failure_mode: FailureMode) -> None:
        """Check if SLO is breached and alert.

        Args:
            failure_mode: The failure mode to check
        """
        rate = self.get_success_rate(failure_mode=failure_mode)

        if rate < self.slo_threshold:
            alert_key = f"slo_breach_{failure_mode.value}"
            now = datetime.now(timezone.utc)

            # Check cooldown
            if alert_key in self._alerts_sent:
                if now - self._alerts_sent[alert_key] < self._alert_cooldown:
                    return

            self._alerts_sent[alert_key] = now

            if self.alert_callback:
                self.alert_callback(
                    "SLO_BREACH",
                    {
                        "failure_mode": failure_mode.value,
                        "success_rate": rate,
                        "threshold": self.slo_threshold,
                        "window_size": self.window_size,
                    },
                )

            logger.warning(
                f"Repair SLO breach: {failure_mode.value} success rate "
                f"{rate:.1%} < {self.slo_threshold:.1%}"
            )

    def identify_problematic_patterns(self) -> List[Dict[str, Any]]:
        """Identify failure modes with consistently low success.

        Returns:
            List of problematic patterns with details
        """
        problematic = []
        metrics = self.get_metrics()

        for mode, stats in metrics.by_failure_mode.items():
            if stats["total"] >= 5:  # Minimum sample size
                rate = stats["success"] / stats["total"]
                if rate < self.slo_threshold:
                    problematic.append({
                        "type": "failure_mode",
                        "name": mode.value,
                        "success_rate": rate,
                        "sample_size": stats["total"],
                    })

        for strategy, stats in metrics.by_strategy.items():
            if stats["total"] >= 5:
                rate = stats["success"] / stats["total"]
                if rate < self.slo_threshold:
                    problematic.append({
                        "type": "strategy",
                        "name": strategy,
                        "success_rate": rate,
                        "sample_size": stats["total"],
                    })

        return sorted(problematic, key=lambda x: x["success_rate"])
