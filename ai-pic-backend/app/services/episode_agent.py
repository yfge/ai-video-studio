from __future__ import annotations

import json
from typing import Any, Dict, Optional, TYPE_CHECKING

from app.core.logging import get_logger
from app.schemas.generation import (
    EpisodePlanItem,
    EpisodePlanModel,
    EpisodeStepOutlineModel,
)
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

        outline_schema = EpisodeStepOutlineModel.model_json_schema()
        plan_schema = EpisodePlanModel.model_json_schema()

        def _extract_missing_fields(exc: Exception) -> list[str]:
            try:
                return ["/".join(map(str, err.get("loc", []))) for err in exc.errors()]
            except Exception:
                return []

        def _normalize_episode_numbers(outlines: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
            normalized = sorted(
                [o for o in outlines if isinstance(o, dict)],
                key=lambda x: x.get("episode_number") or 0,
            )
            for idx, item in enumerate(normalized, start=1):
                item.setdefault("episode_number", idx)
                beats = item.get("beats") or []
                for b_idx, beat in enumerate(beats, start=1):
                    if isinstance(beat, dict):
                        beat.setdefault("sequence_number", b_idx)
                item["beats"] = beats
            return normalized

        outline_variables = {
            "story": story,
            "episode_count": episode_count,
            "episode_duration": episode_duration,
            "focus_characters": focus_characters or [],
            "plot_complexity": plot_complexity,
            "pacing": pacing,
            "additional_requirements": additional_requirements,
            "style_preferences": style_preferences or [],
        }

        graph = StateGraph(dict)

        async def outline_node(state: Dict[str, Any]) -> Dict[str, Any]:
            prompt = prompt_manager.render_prompt(
                PromptTemplate.EPISODE_STEP_OUTLINE.value, outline_variables
            )
            resp = await self.service.ai_manager.generate_text(
                prompt=prompt,
                temperature=min(0.6, temperature),
                model=model,
                prefer_provider=prefer_provider,
                json_schema={"name": "episode_step_outline", "schema": outline_schema},
                system_prompt=prompt_manager.render_prompt(
                    PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
                ),
            )
            content = (
                resp.data
                if isinstance(resp.data, str)
                else ("" if resp.data is None else str(resp.data))
            )
            reasoning = ["outline_ok"] if resp.success else ["outline_failed"]
            return {
                "outline_prompt": prompt,
                "outline_content": content,
                "outline_provider": resp.provider,
                "outline_model": resp.model,
                "outline_usage": resp.usage,
                "reasoning": reasoning,
            }

        def outline_validate_node(state: Dict[str, Any]) -> Dict[str, Any]:
            content = state.get("outline_content") or ""
            reasoning = list(state.get("reasoning", []))
            parsed = (
                extract_json_block(content)
                if isinstance(content, str)
                else (content if isinstance(content, dict) else None)
            )
            missing_fields: list[str] = []
            if parsed:
                try:
                    validated = EpisodeStepOutlineModel.model_validate(parsed)
                    outlines = validated.model_dump()
                    episodes = _normalize_episode_numbers(outlines.get("episodes", []))
                    if len(episodes) < episode_count:
                        reasoning.append("outline_too_short")
                        return {
                            "needs_outline_repair": True,
                            "outline_raw": content,
                            "reasoning": reasoning,
                        }
                    outlines["episodes"] = episodes[:episode_count]
                    reasoning.append("outline_validated")
                    return {
                        "step_outlines_normalized": outlines,
                        "step_outlines_raw": content,
                        "reasoning": reasoning,
                        "needs_outline_repair": False,
                    }
                except Exception as exc:  # pragma: no cover - schema guard
                    missing_fields = _extract_missing_fields(exc)
                    reasoning.append("outline_schema_invalid")
            else:
                reasoning.append("outline_parse_failed")

            return {
                "needs_outline_repair": True,
                "outline_raw": content,
                "missing_fields": missing_fields,
                "reasoning": reasoning,
            }

        async def outline_repair_node(state: Dict[str, Any]) -> Dict[str, Any]:
            if not state.get("needs_outline_repair"):
                return state

            latest_text = state.get("outline_raw") or state.get("outline_content") or ""
            reasoning = list(state.get("reasoning", []))
            missing_fields = state.get("missing_fields") or []
            provider_used = state.get("outline_provider")
            model_used = state.get("outline_model")
            usage = state.get("outline_usage")

            for attempt in range(3):
                parsed = (
                    extract_json_block(latest_text)
                    if isinstance(latest_text, str)
                    else (latest_text if isinstance(latest_text, dict) else None)
                )
                if parsed:
                    try:
                        validated = EpisodeStepOutlineModel.model_validate(parsed)
                        outlines = validated.model_dump()
                        episodes = _normalize_episode_numbers(outlines.get("episodes", []))
                        if len(episodes) >= episode_count:
                            outlines["episodes"] = episodes[:episode_count]
                            reasoning.append(f"outline_repaired_{attempt}")
                            return {
                                "step_outlines_normalized": outlines,
                                "step_outlines_raw": latest_text,
                                "outline_provider": provider_used,
                                "outline_model": model_used,
                                "outline_usage": usage,
                                "reasoning": reasoning,
                                "needs_outline_repair": False,
                            }
                        reasoning.append(f"outline_insufficient_{attempt}")
                    except Exception as exc:  # pragma: no cover - schema guard
                        missing_fields = _extract_missing_fields(exc)
                        reasoning.append(f"outline_schema_invalid_{attempt}")

                repair_prompt = prompt_manager.render_prompt(
                    PromptTemplate.EPISODE_STEP_OUTLINE_REPAIR.value,
                    {
                        "schema": outline_schema,
                        "original_prompt": state.get("outline_prompt"),
                        "original_output": latest_text,
                        "missing_fields": missing_fields,
                        "episode_count": episode_count,
                    },
                )
                resp = await self.service.ai_manager.generate_text(
                    prompt=repair_prompt,
                    temperature=min(0.6, temperature),
                    model=model,
                    prefer_provider=prefer_provider,
                    json_schema={
                        "name": "episode_step_outline_repair",
                        "schema": outline_schema,
                    },
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
                reasoning.append(f"outline_repair_attempt_{attempt + 1}")

            return {
                "error": "outline_invalid",
                "reasoning": reasoning + ["outline_invalid"],
            }

        async def episodes_node(state: Dict[str, Any]) -> Dict[str, Any]:
            outlines = state.get("step_outlines_normalized") or {}
            outline_episodes = outlines.get("episodes") or []
            if not outline_episodes:
                return {
                    "error": "outline_missing",
                    "reasoning": state.get("reasoning", []) + ["outline_missing"],
                }

            provider_used = state.get("outline_provider")
            model_used = state.get("outline_model")
            usage = state.get("outline_usage")
            reasoning = list(state.get("reasoning", []))
            episodes_payload: list[Dict[str, Any]] = []
            episode_contents: list[str] = []

            for outline in outline_episodes[:episode_count]:
                prompt = prompt_manager.render_prompt(
                    PromptTemplate.EPISODE_FROM_OUTLINE.value,
                    {
                        "story": story,
                        "outline": outline,
                        "episode_duration": episode_duration,
                        "plot_complexity": plot_complexity,
                        "pacing": pacing,
                        "additional_requirements": additional_requirements,
                        "style_preferences": style_preferences or [],
                    },
                )
                resp = await self.service.ai_manager.generate_text(
                    prompt=prompt,
                    temperature=temperature,
                    model=model,
                    prefer_provider=prefer_provider,
                    json_schema={"name": "episode_plan", "schema": plan_schema},
                    system_prompt=prompt_manager.render_prompt(
                        PromptTemplate.SYSTEM_PROMPT_SCRIPT.value, {}
                    ),
                )
                content = (
                    resp.data
                    if isinstance(resp.data, str)
                    else ("" if resp.data is None else str(resp.data))
                )
                parsed = (
                    extract_json_block(content)
                    if isinstance(content, str)
                    else (content if isinstance(content, dict) else None)
                )
                episode_obj = None
                if parsed and isinstance(parsed, dict):
                    episodes_arr = parsed.get("episodes") if "episodes" in parsed else None
                    if isinstance(episodes_arr, list) and episodes_arr:
                        episode_obj = episodes_arr[0]

                if not episode_obj:
                    reasoning.append(
                        f"episode_parse_failed_{outline.get('episode_number', 'na')}"
                    )
                    continue

                episode_obj.setdefault("episode_number", outline.get("episode_number"))
                try:
                    EpisodePlanItem.model_validate(episode_obj)
                    episodes_payload.append(episode_obj)
                    episode_contents.append(content)
                    provider_used = resp.provider or provider_used
                    model_used = resp.model or model_used
                    usage = resp.usage or usage
                    reasoning.append(
                        f"episode_ok_{outline.get('episode_number', len(episodes_payload))}"
                    )
                except Exception as exc:  # pragma: no cover - schema guard
                    missing_fields = _extract_missing_fields(exc)
                    self.logger.info(
                        "Episode item validation failed",
                        extra={
                            "episode": outline.get("episode_number"),
                            "missing": missing_fields,
                        },
                    )
                    reasoning.append(
                        f"episode_invalid_{outline.get('episode_number', 'na')}"
                    )

            if len(episodes_payload) < episode_count:
                return {
                    "error": "episodes_incomplete",
                    "reasoning": reasoning + ["episodes_incomplete"],
                    "step_outlines_normalized": outlines,
                    "step_outlines_raw": state.get("step_outlines_raw"),
                }

            return {
                "content": json.dumps(
                    {"episodes": episodes_payload}, ensure_ascii=False
                ),
                "normalized": {"episodes": episodes_payload},
                "step_outlines": outlines,
                "step_outlines_raw": state.get("step_outlines_raw"),
                "step_outline_prompt": state.get("outline_prompt"),
                "generation_method": "langgraph_episode_step_outline",
                "template_used": PromptTemplate.EPISODE_FROM_OUTLINE.value,
                "provider_used": provider_used,
                "model_used": model_used,
                "usage": usage,
                "reasoning": reasoning + ["episodes_done"],
            }

        graph.add_node("outline", outline_node)
        graph.add_node("outline_validate", outline_validate_node)
        graph.add_node("outline_repair", outline_repair_node)
        graph.add_node("episodes", episodes_node)
        graph.add_edge("outline", "outline_validate")
        graph.add_edge("outline_validate", "outline_repair")
        graph.add_edge("outline_repair", "episodes")
        graph.add_edge("episodes", END)
        graph.set_entry_point("outline")

        app = graph.compile()
        return await app.ainvoke({})
