from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from app.core.logging import get_logger
from app.prompts.templates import PromptTemplate

from .episode_agent_episode import dumps_episode_payload, generate_episodes_from_outlines
from .episode_agent_outline import generate_step_outlines

try:  # pragma: no cover - optional dependency
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    END = "END"
    StateGraph = None  # type: ignore[assignment]
    LANGGRAPH_AVAILABLE = False

if TYPE_CHECKING:
    from .ai_service import AIService


@dataclass(slots=True)
class EpisodeGenerationCallbacks:
    """Optional hooks for streaming progress/persistence during agent execution."""

    on_progress: Callable[[str], Any] | None = None
    on_outline: Callable[[dict[str, Any], dict[str, Any]], Any] | None = None
    on_episode: Callable[[dict[str, Any], dict[str, Any]], Any] | None = None


async def _maybe_await(
    callback: Callable[..., Any] | None, *args: Any, **kwargs: Any
) -> Any:
    if not callback:
        return None
    result = callback(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


class EpisodeLangGraphAgent:
    """LangGraph-compatible episode generator with strict outline validation."""

    def __init__(self, service: "AIService") -> None:
        self.service = service
        self.logger = get_logger()

    async def generate(
        self,
        *,
        story: Dict[str, Any],
        episode_count: int,
        episode_duration: Optional[int],
        focus_characters: Optional[list[Dict[str, Any]]],
        plot_complexity: str,
        pacing: str,
        additional_requirements: Optional[str],
        style_preferences: Optional[list[str]],
        model: Optional[str],
        prefer_provider: Optional[str],
        temperature: float,
        callbacks: EpisodeGenerationCallbacks | None = None,
    ) -> Optional[Dict[str, Any]]:
        if not LANGGRAPH_AVAILABLE or not getattr(self.service, "ai_manager", None):
            return None

        async def _progress(message: str) -> None:
            await _maybe_await(callbacks.on_progress if callbacks else None, message)

        outline_result = await generate_step_outlines(
            ai_manager=self.service.ai_manager,
            story=story,
            episode_count=episode_count,
            episode_duration=episode_duration,
            focus_characters=focus_characters or [],
            plot_complexity=plot_complexity,
            pacing=pacing,
            additional_requirements=additional_requirements,
            style_preferences=style_preferences or [],
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
            progress=_progress,
        )

        reasoning = outline_result.reasoning
        if outline_result.error or not outline_result.step_outlines:
            return {
                "error": outline_result.error or "outline_invalid",
                "reasoning": reasoning + [outline_result.error or "outline_invalid"],
            }

        await _maybe_await(
            callbacks.on_outline if callbacks else None,
            outline_result.step_outlines,
            {
                "prompt": outline_result.prompt,
                "raw": outline_result.raw_text,
                "provider": outline_result.provider,
                "model": outline_result.model,
                "usage": outline_result.usage,
                "reasoning": reasoning,
                "generation_method": "langgraph_episode_step_outline",
            },
        )

        async def _emit_episode(episode_obj: Dict[str, Any], meta: Dict[str, Any]) -> None:
            await _maybe_await(
                callbacks.on_episode if callbacks else None, episode_obj, meta
            )

        episode_result = await generate_episodes_from_outlines(
            ai_manager=self.service.ai_manager,
            story=story,
            step_outlines=outline_result.step_outlines,
            episode_count=episode_count,
            episode_duration=episode_duration,
            focus_characters=focus_characters or [],
            plot_complexity=plot_complexity,
            pacing=pacing,
            additional_requirements=additional_requirements,
            style_preferences=style_preferences or [],
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
            progress=_progress,
            emit_episode=_emit_episode,
            reasoning=reasoning,
            initial_provider=outline_result.provider,
            initial_model=outline_result.model,
            initial_usage=outline_result.usage,
        )

        return {
            "content": dumps_episode_payload(episode_result.episodes),
            "normalized": {"episodes": episode_result.episodes},
            "step_outlines": outline_result.step_outlines,
            "step_outlines_raw": outline_result.raw_text,
            "step_outline_prompt": outline_result.prompt,
            "prompt": outline_result.prompt,
            "generation_method": "langgraph_episode_step_outline",
            "template_used": PromptTemplate.EPISODE_FROM_OUTLINE.value,
            "provider_used": episode_result.provider,
            "model_used": episode_result.model,
            "usage": episode_result.usage,
            "reasoning": episode_result.reasoning + ["episodes_done"],
        }
