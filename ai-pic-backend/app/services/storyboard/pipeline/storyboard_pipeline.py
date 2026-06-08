"""
Main LangGraph pipeline for storyboard generation with React validation.

Orchestrates the complete storyboard generation workflow:
precheck → generate_plan → validate_plan → generate_frames → validate → finalize
"""

from __future__ import annotations

from importlib.util import find_spec
from typing import TYPE_CHECKING, Any, Dict, Optional

from app.core.logging import get_logger
from app.services.storyboard.pipeline.execution_mixin import (
    StoryboardPipelineExecutionMixin,
)
from app.services.storyboard.pipeline.pipeline_context import build_pipeline_context
from app.services.storyboard.pipeline.pipeline_state import PipelineState
from app.services.storyboard.pipeline.plan_mixin import StoryboardPipelinePlanMixin
from app.services.storyboard.pipeline.validation_mixin import (
    StoryboardPipelineValidationMixin,
)
from app.services.storyboard.recovery.incremental_repair import IncrementalRepair
from app.services.storyboard.recovery.retry_strategy import RetryStrategy
from app.services.storyboard.sync.data_precheck import DataPrecheck
from app.services.storyboard.validators import (
    CharacterPresenceValidator,
    CinematicRulesValidator,
    ConsistencyValidator,
    FrameIntegrityValidator,
    TimelineValidator,
)

LANGGRAPH_AVAILABLE = find_spec("langgraph") is not None

if TYPE_CHECKING:
    from app.models.script import Episode, Script
    from app.services.ai_service import AIService
    from sqlalchemy.orm import Session


class StoryboardPipeline(
    StoryboardPipelineExecutionMixin,
    StoryboardPipelinePlanMixin,
    StoryboardPipelineValidationMixin,
):
    """
    LangGraph-based storyboard generation pipeline with React validation.

    Pipeline stages:
    1. precheck - Validate data availability
    2. generate_plan - Create storyboard plan
    3. validate_plan - ConsistencyValidator
    4. generate_frames - Generate storyboard frames
    5. validate_frames - FrameIntegrityValidator + CharacterPresenceValidator + CinematicRulesValidator
    6. validate_timeline - TimelineValidator
    7. recovery - Repair issues if needed
    8. finalize - Persist results
    """

    def __init__(
        self,
        db: "Session",
        ai_service: Optional["AIService"] = None,
    ):
        self.db = db
        self.ai_service = ai_service
        self.logger = get_logger()

        self.precheck = DataPrecheck(db)
        self.retry_strategy = RetryStrategy()
        self.repair = IncrementalRepair()
        self.validators = {
            "consistency": ConsistencyValidator(),
            "timeline": TimelineValidator(),
            "frame_integrity": FrameIntegrityValidator(),
            "character_presence": CharacterPresenceValidator(),
            "cinematic_rules": CinematicRulesValidator(),
        }

    async def generate(
        self,
        *,
        script: "Script",
        episode: Optional["Episode"] = None,
        frames_per_scene: int = 4,
        selected_scenes: Optional[list[int]] = None,
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.7,
        max_frames: Optional[int] = None,
        use_langgraph: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute the storyboard generation pipeline.

        Args:
            script: Script model instance
            episode: Optional Episode for audio-based generation
            frames_per_scene: Target frames per scene
            selected_scenes: Optional list of scene numbers to generate
            model: AI model to use
            prefer_provider: Preferred AI provider
            temperature: Generation temperature
            max_frames: Maximum total frames
            use_langgraph: Whether to use LangGraph orchestration

        Returns:
            Dictionary with generated frames and metadata
        """
        context = build_pipeline_context(
            self.db,
            script=script,
            episode=episode,
        )
        state = PipelineState(
            script_id=script.id,
            episode_id=episode.id if episode else None,
            frames_per_scene=frames_per_scene,
            selected_scenes=selected_scenes,
            temperature=temperature,
        )
        state.model = model
        state.prefer_provider = prefer_provider
        state.max_frames = max_frames

        if use_langgraph and LANGGRAPH_AVAILABLE:
            return await self._execute_langgraph(state, context, script, episode)
        return await self._execute_sequential(state, context, script, episode)


__all__ = ["StoryboardPipeline", "LANGGRAPH_AVAILABLE"]
