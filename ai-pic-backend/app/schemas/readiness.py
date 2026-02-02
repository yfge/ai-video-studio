"""
Readiness check schemas for story/episode generation validation.

These schemas define the structure for pre-generation readiness checks
that validate all prerequisites before starting generation tasks.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, computed_field


class ReadinessSeverity(str, Enum):
    """Severity levels for readiness checks."""

    CRITICAL = "CRITICAL"  # Blocks generation
    ERROR = "ERROR"  # Strongly recommended to fix
    WARNING = "WARNING"  # May affect quality
    INFO = "INFO"  # Suggestions for improvement


class ReadinessCheck(BaseModel):
    """Result of a single readiness check."""

    name: str = Field(..., description="Check identifier (e.g., 'title_present')")
    passed: bool = Field(..., description="Whether the check passed")
    severity: Literal["CRITICAL", "ERROR", "WARNING", "INFO"] = Field(
        ..., description="Severity level of this check"
    )
    message: str = Field(..., description="Human-readable result message")
    suggestion: Optional[str] = Field(
        None, description="Suggested action if check failed"
    )


class ReadinessResult(BaseModel):
    """Aggregate result of all readiness checks."""

    ready: bool = Field(
        ..., description="True if no CRITICAL or ERROR issues (safe to proceed)"
    )
    can_proceed: bool = Field(
        ..., description="True if no CRITICAL issues (generation possible but risky)"
    )
    story_id: int = Field(..., description="ID of the checked story")
    episode_id: Optional[int] = Field(
        None, description="ID of the checked episode (if episode-level check)"
    )
    checks: list[ReadinessCheck] = Field(
        default_factory=list, description="All check results"
    )
    summary: str = Field(..., description="Human-readable summary of readiness state")

    @computed_field
    @property
    def critical_issues(self) -> list[ReadinessCheck]:
        """Return all failed CRITICAL checks."""
        return [c for c in self.checks if not c.passed and c.severity == "CRITICAL"]

    @computed_field
    @property
    def errors(self) -> list[ReadinessCheck]:
        """Return all failed ERROR checks."""
        return [c for c in self.checks if not c.passed and c.severity == "ERROR"]

    @computed_field
    @property
    def warnings(self) -> list[ReadinessCheck]:
        """Return all failed WARNING checks."""
        return [c for c in self.checks if not c.passed and c.severity == "WARNING"]

    @computed_field
    @property
    def info_issues(self) -> list[ReadinessCheck]:
        """Return all failed INFO checks."""
        return [c for c in self.checks if not c.passed and c.severity == "INFO"]

    @computed_field
    @property
    def failed_count(self) -> int:
        """Count of all failed checks."""
        return sum(1 for c in self.checks if not c.passed)

    @computed_field
    @property
    def passed_count(self) -> int:
        """Count of all passed checks."""
        return sum(1 for c in self.checks if c.passed)


class FixApplied(BaseModel):
    """Record of a fix that was applied."""

    check_name: str = Field(..., description="Name of the check that was fixed")
    field: str = Field(..., description="Field that was updated")
    old_value: Optional[Any] = Field(None, description="Previous value")
    new_value: Any = Field(..., description="New value after fix")


class FixSkipped(BaseModel):
    """Record of a fix that was skipped."""

    check_name: str = Field(..., description="Name of the check that was skipped")
    reason: str = Field(..., description="Reason why fix was skipped")


class QuickFixImprovement(BaseModel):
    """Summary of improvement after quick-fix."""

    initial_failed: int = Field(..., description="Failed checks before fix")
    final_failed: int = Field(..., description="Failed checks after fix")
    fixed_count: int = Field(..., description="Number of fixes applied")


class QuickFixRequest(BaseModel):
    """Request body for quick-fix endpoint."""

    dry_run: bool = Field(
        False, description="If true, only report what would be fixed without applying"
    )


class QuickFixResponse(BaseModel):
    """Response from quick-fix endpoint."""

    story_id: int = Field(..., description="ID of the story that was fixed")
    dry_run: bool = Field(..., description="Whether this was a dry run")
    fixes_applied: list[FixApplied] = Field(
        default_factory=list, description="Fixes that were applied"
    )
    fixes_skipped: list[FixSkipped] = Field(
        default_factory=list, description="Fixes that were skipped"
    )
    initial_readiness: ReadinessResult = Field(
        ..., description="Readiness state before fixes"
    )
    final_readiness: ReadinessResult = Field(
        ..., description="Readiness state after fixes"
    )
    improvement: QuickFixImprovement = Field(
        ..., description="Summary of improvement"
    )
