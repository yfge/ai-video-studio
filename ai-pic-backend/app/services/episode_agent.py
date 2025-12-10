from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

from app.core.logging import get_logger
from app.schemas.generation import EpisodePlanModel
from app.utils.json_utils import extract_json_block
from app.prompts.templates import PromptTemplate
from app.prompts.manager import prompt_manager

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

        schema = EpisodePlanModel.model_json_schema()

        def _extract_missing_fields(exc: Exception) -> list[str]:
            try:
                return ["/".join(map(str, err.get("loc", []))) for err in exc.errors()]
            except Exception:
                return []

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

        async def repair_node(state: Dict[str, Any]) -> Dict[str, Any]:
            res = state.get("result") or {}
            content = res.get("content")
            reasoning = list(state.get("reasoning", []))
            provider_used = res.get("provider_used")
            model_used = res.get("model_used")
            usage = res.get("usage")
            latest_text = (
                content
                if isinstance(content, str)
                else ("" if content is None else str(content))
            )

            for attempt in range(3):
                parsed = (
                    extract_json_block(latest_text)
                    if isinstance(latest_text, str)
                    else (latest_text if isinstance(latest_text, dict) else None)
                )
                if parsed:
                    try:
                        EpisodePlanModel.model_validate(parsed)
                        reasoning.append(f"validated_attempt_{attempt}")
                        res["normalized"] = parsed
                        res["content"] = latest_text
                        res["generation_method"] = res.get("generation_method") or "langgraph_episode"
                        res["provider_used"] = provider_used
                        res["model_used"] = model_used
                        res["usage"] = usage
                        res["reasoning"] = reasoning + ["done"]
                        return res
                    except Exception as exc:  # pragma: no cover - schema guard
                        missing_fields = _extract_missing_fields(exc)
                        reasoning.append(f"schema_invalid_attempt_{attempt}")
                        self.logger.info(
                            "Episode validation failed; repairing",
                            extra={"attempt": attempt, "missing": missing_fields},
                        )
                else:
                    reasoning.append(f"parse_failed_attempt_{attempt}")
                    self.logger.info(
                        "Episode parse failed; repairing", extra={"attempt": attempt}
                    )

                if attempt >= 2:
                    break

                repair_prompt = prompt_manager.render_prompt(
                    PromptTemplate.EPISODE_PLAN_REPAIR.value,
                    {
                        "schema": schema,
                        "original_prompt": res.get("prompt"),
                        "original_output": latest_text,
                        "missing_fields": missing_fields if parsed else [],
                    },
                )
                resp = await self.service.ai_manager.generate_text(
                    prompt=repair_prompt,
                    temperature=temperature,
                    model=model,
                    prefer_provider=prefer_provider,
                    json_schema={"name": "episode_plan_repair", "schema": schema},
                    system_prompt=prompt_manager.render_prompt(
                        PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
                    ),
                )
                latest_text = (
                    resp.data
                    if isinstance(resp.data, str)
                    else ("" if resp.data is None else str(resp.data))
                )
                provider_used = resp.provider or provider_used
                model_used = resp.model or model_used
                usage = resp.usage or usage
                reasoning.append(f"repair_attempt_{attempt + 1}")

            return {
                "error": "episodes_invalid",
                "reasoning": reasoning + ["episodes_invalid"],
                "content": content,
            }

        graph.add_node("plan", plan_node)
        graph.add_node("repair", repair_node)
        graph.add_edge("plan", "repair")
        graph.add_edge("repair", END)
        graph.set_entry_point("plan")

        app = graph.compile()
        return await app.ainvoke({})
