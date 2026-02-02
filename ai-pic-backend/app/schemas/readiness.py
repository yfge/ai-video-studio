"""
Readiness check schemas for story/episode generation validation.

These schemas define the structure for pre-generation readiness checks
that validate all prerequisites before starting generation tasks.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

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
