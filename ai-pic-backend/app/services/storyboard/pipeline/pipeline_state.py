"""
Pipeline state definitions for storyboard generation.

Defines state machine phases, validation results, and the core state
dataclass used throughout the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def _utcnow() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)
from typing import Any


class PipelinePhase(str, Enum):
    """Pipeline execution phases."""

    PRECHECK = "precheck"
    SYNC_STRUCTURE = "sync_structure"
    GENERATE_PLAN = "generate_plan"
    VALIDATE_PLAN = "validate_plan"
    GENERATE_FRAMES = "generate_frames"
    VALIDATE_FRAMES = "validate_frames"
    ASSEMBLE_TIMELINE = "assemble_timeline"
    VALIDATE_TIMELINE = "validate_timeline"
    FINAL_VALIDATION = "final_validation"
    RECOVERY = "recovery"
    FINALIZE = "finalize"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a validation check."""

    validator_name: str
    passed: bool
    severity: ValidationSeverity = ValidationSeverity.INFO
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "validator_name": self.validator_name,
            "passed": self.passed,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def success(
        cls,
        validator_name: str,
        message: str = "Validation passed",
        details: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Create a successful validation result."""
        return cls(
            validator_name=validator_name,
            passed=True,
            severity=ValidationSeverity.INFO,
            message=message,
            details=details or {},
        )

    @classmethod
    def warning(
        cls,
        validator_name: str,
        message: str,
        details: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
    ) -> ValidationResult:
        """Create a warning validation result."""
        return cls(
            validator_name=validator_name,
            passed=True,
            severity=ValidationSeverity.WARNING,
            message=message,
            details=details or {},
            suggestions=suggestions or [],
        )

    @classmethod
    def error(
        cls,
        validator_name: str,
        message: str,
        details: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
    ) -> ValidationResult:
        """Create an error validation result."""
        return cls(
            validator_name=validator_name,
            passed=False,
            severity=ValidationSeverity.ERROR,
            message=message,
            details=details or {},
            suggestions=suggestions or [],
        )

    @classmethod
    def critical(
        cls,
        validator_name: str,
        message: str,
        details: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
    ) -> ValidationResult:
        """Create a critical validation result."""
        return cls(
            validator_name=validator_name,
            passed=False,
            severity=ValidationSeverity.CRITICAL,
            message=message,
            details=details or {},
            suggestions=suggestions or [],
        )


@dataclass
class PipelineState:
    """
    State object passed through the storyboard generation pipeline.

    Tracks current phase, validation results, generated artifacts,
    and recovery attempts.
    """

    # Core identifiers
    script_id: int
    episode_id: int | None = None

    # Current phase
    phase: PipelinePhase = PipelinePhase.PRECHECK

    # Validation tracking
    validation_results: list[ValidationResult] = field(default_factory=list)
    has_errors: bool = False
    has_warnings: bool = False

    # Generated artifacts
    plan: dict[str, Any] | None = None
    frames: list[dict[str, Any]] = field(default_factory=list)
    timeline: dict[str, Any] | None = None

    # Recovery tracking
    recovery_attempts: int = 0
    max_recovery_attempts: int = 2
    recovery_history: list[dict[str, Any]] = field(default_factory=list)

    # Execution metadata
    started_at: datetime = field(default_factory=_utcnow)
    completed_at: datetime | None = None
    reasoning_trace: list[str] = field(default_factory=list)

    # Provider info
    provider_used: str | None = None
    model_used: str | None = None
    usage: dict[str, Any] | None = None

    # Configuration
    frames_per_scene: int = 4
    selected_scenes: list[int] | None = None
    temperature: float = 0.7

    def add_validation(self, result: ValidationResult) -> None:
        """Add a validation result and update error/warning flags."""
        self.validation_results.append(result)
        if not result.passed:
            if result.severity == ValidationSeverity.CRITICAL:
                self.has_errors = True
            elif result.severity == ValidationSeverity.ERROR:
                self.has_errors = True
        if result.severity == ValidationSeverity.WARNING:
            self.has_warnings = True

    def add_reasoning(self, step: str) -> None:
        """Add a reasoning trace step."""
        self.reasoning_trace.append(step)

    def can_recover(self) -> bool:
        """Check if recovery is still possible."""
        return self.recovery_attempts < self.max_recovery_attempts

    def record_recovery(self, action: str, details: dict[str, Any]) -> None:
        """Record a recovery attempt."""
        self.recovery_attempts += 1
        self.recovery_history.append(
            {
                "attempt": self.recovery_attempts,
                "action": action,
                "details": details,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def get_failed_validations(self) -> list[ValidationResult]:
        """Get all failed validation results."""
        return [v for v in self.validation_results if not v.passed]

    def get_warnings(self) -> list[ValidationResult]:
        """Get all warning validation results."""
        return [
            v
            for v in self.validation_results
            if v.severity == ValidationSeverity.WARNING
        ]

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "script_id": self.script_id,
            "episode_id": self.episode_id,
            "phase": self.phase.value,
            "validation_results": [v.to_dict() for v in self.validation_results],
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
            "plan": self.plan,
            "frames_count": len(self.frames),
            "timeline": self.timeline,
            "recovery_attempts": self.recovery_attempts,
            "recovery_history": self.recovery_history,
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "reasoning_trace": self.reasoning_trace,
            "provider_used": self.provider_used,
            "model_used": self.model_used,
        }
