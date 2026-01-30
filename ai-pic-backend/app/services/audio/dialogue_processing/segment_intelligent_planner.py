"""Intelligent segment planning for a scene (with optional duration target)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Sequence

from app.core.logging import get_logger

from .segment_builder import _build_segments_with_timing
from .segment_models import PlannedSegment
from .segment_padding import _pad_segments_to_target_duration_ms

if TYPE_CHECKING:
    from app.services.ai_service import AIService

logger = get_logger()


async def plan_scene_segments_intelligent(
    *,
    dialogues: Sequence[dict[str, Any]],
    stage_directions: Sequence[dict[str, Any]],
    scene_context: dict[str, Any],
    ai_service: Optional["AIService"] = None,
    use_intelligent_timing: bool = True,
    pause_after_dialogue_ms: int = 300,
    action_base_ms: int = 800,
    action_per_char_ms: int = 20,
    action_max_ms: int = 3000,
    timing_model: Optional[str] = None,
    prefer_provider: Optional[str] = None,
    target_duration_seconds: Optional[int] = None,
) -> list[PlannedSegment]:
    """Build an ordered segment plan with intelligent gap calculation."""

    timing_map: dict[int, int] = {}

    if use_intelligent_timing and ai_service:
        try:
            from app.services.timeline_agent import TimelineLangGraphAgent

            agent = TimelineLangGraphAgent(ai_service)
            timing_plan = await agent.compute_timing(
                dialogues=list(dialogues),
                stage_directions=list(stage_directions),
                scene_context=scene_context,
                model=timing_model,
                prefer_provider=prefer_provider,
                target_duration_seconds=target_duration_seconds,
            )

            if timing_plan and timing_plan.decisions:
                for decision in timing_plan.decisions:
                    timing_map[decision.segment_index] = decision.adjusted_duration_ms
                logger.info(
                    "Intelligent timing computed: %s decisions, avg=%sms, fallback=%s",
                    len(timing_map),
                    f"{timing_plan.avg_gap_ms:.0f}",
                    timing_plan.fallback_used,
                )
        except Exception as exc:
            logger.warning("Intelligent timing failed, using fallback: %s", exc)

    segments = _build_segments_with_timing(
        dialogues=dialogues,
        stage_directions=stage_directions,
        timing_map=timing_map,
        pause_after_dialogue_ms=pause_after_dialogue_ms,
        action_base_ms=action_base_ms,
        action_per_char_ms=action_per_char_ms,
        action_max_ms=action_max_ms,
    )

    if target_duration_seconds:
        segments = _pad_segments_to_target_duration_ms(
            segments=segments,
            dialogues=dialogues,
            target_duration_ms=int(target_duration_seconds * 1000),
            scene_context=scene_context,
        )

    return segments
