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

        async def _validate_and_repair(
            content: Any,
            *,
            base_reasoning: list[str],
        ) -> Optional[Dict[str, Any]]:
            """Parse + schema-validate, with up to 2 repair attempts via ReAct-style hints."""
            reasoning = list(base_reasoning)
            provider_used = None
            model_used = None
            usage = None
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
                        return {
                            "normalized": parsed,
                            "content": latest_text,
                            "provider_used": provider_used,
                            "model_used": model_used,
                            "usage": usage,
                            "reasoning": reasoning,
                        }
                    except Exception as exc:  # pragma: no cover - schema guard
                        error_msg = str(exc)
                        reasoning.append(f"schema_invalid_attempt_{attempt}:{error_msg}")
                        self.logger.info(
                            "LangGraph episode validation failed; retrying",
                            extra={"attempt": attempt, "error": error_msg},
                        )
                else:
                    reasoning.append(f"parse_failed_attempt_{attempt}")
                    self.logger.info(
                        "LangGraph episode parse failed; retrying",
                        extra={"attempt": attempt},
                    )

                if attempt >= 2:
                    break

                repair_prompt = (
                    "以下是一次剧集规划的原始输出，需修复为满足 EpisodePlanModel Schema 的纯 JSON。"
                    " 请补齐 episodes 数组及必需字段（episode_number/title/summary/plot_points/conflicts/character_arcs），"
                    " 保持原有信息并用中文，严格只输出 JSON：\n"
                    f"Schema: {schema}\n"
                    f"原始输出:\n{latest_text}"
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

        async def finalize_node(state: Dict[str, Any]) -> Dict[str, Any]:
            res = state.get("result") or {}
            content = res.get("content")
            validation = await _validate_and_repair(
                content, base_reasoning=state.get("reasoning", [])
            )
            if not validation:
                return {
                    "error": "episodes_invalid",
                    "reasoning": state.get("reasoning", []) + ["episodes_invalid"],
                    "content": res.get("content"),
                }

            res["normalized"] = validation["normalized"]
            res["content"] = validation["content"]
            res["generation_method"] = res.get("generation_method") or "langgraph_episode"
            res["provider_used"] = validation.get("provider_used") or res.get("provider_used")
            res["model_used"] = validation.get("model_used") or res.get("model_used")
            res["usage"] = validation.get("usage") or res.get("usage")
            res["reasoning"] = validation.get("reasoning", []) + ["done"]
            return res

        graph.add_node("plan", plan_node)
        graph.add_node("finalize", finalize_node)
        graph.add_edge("plan", "finalize")
        graph.add_edge("finalize", END)
        graph.set_entry_point("plan")

        app = graph.compile()
        return await app.ainvoke({})
