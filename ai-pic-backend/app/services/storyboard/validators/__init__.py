"""
Storyboard validation framework.

Provides React-style validators for storyboard generation pipeline.
Each validator checks specific aspects of data consistency and integrity.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.storyboard.pipeline.pipeline_context import PipelineContext
    from app.services.storyboard.pipeline.pipeline_state import (
        PipelineState,
        ValidationResult,
    )


class BaseValidator(ABC):
    """
    Abstract base class for storyboard validators.

    Validators implement the React pattern - they analyze state,
    identify issues, and provide actionable suggestions for repair.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique validator name for identification."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description of what this validator checks."""
        return ""

    @abstractmethod
    def validate(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        **kwargs: Any,
    ) -> list["ValidationResult"]:
        """
        Run validation and return results.

        Args:
            state: Current pipeline state with frames, plan, etc.
            context: Pipeline context with script/scene data.
            **kwargs: Additional validator-specific parameters.

        Returns:
            List of ValidationResult objects (may be empty if all passes).
        """
        ...

    def can_auto_fix(self) -> bool:
        """Whether this validator can automatically fix issues."""
        return False

    def auto_fix(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        issues: list["ValidationResult"],
    ) -> tuple["PipelineState", list[str]]:
        """
        Attempt to automatically fix issues.

        Args:
            state: Current pipeline state.
            context: Pipeline context.
            issues: List of validation issues to fix.

        Returns:
            Tuple of (modified state, list of fix descriptions).
        """
        return state, []


from app.services.storyboard.validators.character_presence_validator import (
    CharacterPresenceValidator,
)
from app.services.storyboard.validators.consistency_validator import (
    ConsistencyValidator,
)
from app.services.storyboard.validators.frame_integrity_validator import (
    FrameIntegrityValidator,
)
from app.services.storyboard.validators.timeline_validator import TimelineValidator

__all__ = [
    "BaseValidator",
    "CharacterPresenceValidator",
    "ConsistencyValidator",
    "FrameIntegrityValidator",
    "TimelineValidator",
]
