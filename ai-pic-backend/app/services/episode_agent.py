from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

from app.core.logging import get_logger
from app.schemas.generation import EpisodePlanModel
from app.utils.story_parser import extract_json_block

try:
    from langgraph.graph import StateGraph, END

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    LANGGRAPH_AVAILABLE = False

if TYPE_CHECKING:
    from .ai_service import AIService


class EpisodeLangGraphAgent:
    """Lightweight LangGraph agent to orchestrate episode generation."""

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
    ) -> Optional[Dict[str, Any]]:
        if not LANGGRAPH_AVAILABLE or not self.service.ai_manager:
            return None

        graph = StateGraph(dict)

        async def plan_node(state: Dict[str, Any]) -> Dict[str, Any]:
            res = await self.service._call_ai_manager_episode(
                story=story,
                episode_count=episode_count,
                episode_duration=episode_duration,
                focus_characters=focus_characters,
                plot_complexity=plot_complexity,
                pacing=pacing,
                additional_requirements=additional_requirements,
                style_preferences=style_preferences,
                model=model,
                prefer_provider=prefer_provider,
                temperature=temperature,
            )
            if not res:
                return {"error": "plan_failed", "reasoning": ["plan_failed"]}
            return {"result": res, "reasoning": ["plan_ok"]}

        def finalize_node(state: Dict[str, Any]) -> Dict[str, Any]:
            res = state.get("result") or {}
            content = res.get("content")
            normalized = res.get("normalized") if isinstance(res, dict) else None

            if isinstance(content, str):
                parsed = extract_json_block(content)
                if parsed:
                    normalized = parsed
                    res["normalized"] = parsed
            elif isinstance(content, dict):
                normalized = content
                res["normalized"] = content

            episodes = (
                normalized.get("episodes") if isinstance(normalized, dict) else None
            )
            if not episodes:
                return {
                    "error": "episodes_empty",
                    "reasoning": state.get("reasoning", []) + ["episodes_empty"],
                }
            try:
                EpisodePlanModel.model_validate({"episodes": episodes})
            except Exception as exc:  # pragma: no cover - schema guard
                self.logger.warning(f"LangGraph episode validation failed: {exc}")
                return {
                    "error": "episodes_invalid",
                    "reasoning": state.get("reasoning", []) + ["episodes_invalid"],
                    "content": res.get("content"),
                }
            res["generation_method"] = (
                res.get("generation_method") or "langgraph_episode"
            )
            res["reasoning"] = state.get("reasoning", []) + ["done"]
            return res

        graph.add_node("plan", plan_node)
        graph.add_node("finalize", finalize_node)
        graph.add_edge("plan", "finalize")
        graph.add_edge("finalize", END)
        graph.set_entry_point("plan")

        app = graph.compile()
        return await app.ainvoke({})
