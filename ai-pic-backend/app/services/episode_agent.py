from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

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
        callbacks: EpisodeGenerationCallbacks | None = None,
    ) -> Optional[Dict[str, Any]]:
        if not LANGGRAPH_AVAILABLE or not self.service.ai_manager:
            return None

        outline_schema = EpisodeStepOutlineModel.model_json_schema()
        plan_schema = EpisodePlanModel.model_json_schema()

        async def _progress(message: str) -> None:
            await _maybe_await(callbacks.on_progress if callbacks else None, message)

        def _extract_missing_fields(exc: Exception) -> list[str]:
            try:
                return ["/".join(map(str, err.get("loc", []))) for err in exc.errors()]
            except Exception:
                return []

        def _normalize_episode_numbers(
            outlines: list[Dict[str, Any]],
        ) -> list[Dict[str, Any]]:
            normalized = sorted(
                [o for o in outlines if isinstance(o, dict)],
                key=lambda x: x.get("episode_number") or 0,
            )
            for idx, item in enumerate(normalized, start=1):
                item.setdefault("episode_number", idx)
                # beats are optional; keep order if present but don't enforce
                beats = item.get("beats")
                if isinstance(beats, list):
                    for b_idx, beat in enumerate(beats, start=1):
                        if isinstance(beat, dict):
                            beat.setdefault("sequence_number", b_idx)
                    item["beats"] = beats
            return normalized

        def _is_episode_valid(episode_obj: Dict[str, Any]) -> tuple[bool, str | None]:
            """Lightweight sanity checks after schema validation."""
            if not episode_obj.get("summary"):
                return False, "missing_summary"
            conflicts = episode_obj.get("conflicts")
            if not conflicts or not isinstance(conflicts, list):
                return False, "missing_conflicts"
            if any(isinstance(c, dict) for c in conflicts):
                return True, None
            return False, "invalid_conflicts"

        def _stub_episode_from_outline(outline: Dict[str, Any]) -> Dict[str, Any]:
            ep_num = outline.get("episode_number") or 1
            logline = (outline.get("logline") or "").strip() or "本集出现关键转折。"
            title = outline.get("title") or f"第{ep_num}集"
            return {
                "episode_number": ep_num,
                "title": title,
                "summary": logline,
                "plot_points": [],
                "character_arcs": None,
                "conflicts": [{"description": logline, "intensity": "medium"}],
                "scene_count": None,
                "fallback_from_outline": True,
            }

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
            await _progress("剧集大纲：调用模型")
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
                    # 只要求集数与 logline/标题存在
                    filtered = []
                    for ep in episodes:
                        logline = ep.get("logline") or ""
                        if isinstance(logline, str) and logline.strip():
                            filtered.append(ep)
                    if len(filtered) < episode_count:
                        reasoning.append("outline_too_short")
                        return {
                            "needs_outline_repair": True,
                            "outline_raw": content,
                            "reasoning": reasoning,
                        }
                    outlines["episodes"] = filtered[:episode_count]
                    reasoning.append("outline_validated")
                    return {
                        "step_outlines_normalized": outlines,
                        "step_outlines_raw": content,
                        "outline_prompt": state.get("outline_prompt"),
                        "outline_provider": state.get("outline_provider"),
                        "outline_model": state.get("outline_model"),
                        "outline_usage": state.get("outline_usage"),
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
                "outline_prompt": state.get("outline_prompt"),
                "outline_provider": state.get("outline_provider"),
                "outline_model": state.get("outline_model"),
                "outline_usage": state.get("outline_usage"),
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
                        episodes = _normalize_episode_numbers(
                            outlines.get("episodes", [])
                        )
                        filtered = [
                            ep for ep in episodes if (ep.get("logline") or "").strip()
                        ]
                        if len(filtered) >= episode_count:
                            outlines["episodes"] = filtered[:episode_count]
                            reasoning.append(f"outline_repaired_{attempt}")
                            return {
                                "step_outlines_normalized": outlines,
                                "step_outlines_raw": latest_text,
                                "outline_provider": provider_used,
                                "outline_model": model_used,
                                "outline_usage": usage,
                                "outline_prompt": state.get("outline_prompt"),
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

            await _maybe_await(
                callbacks.on_outline if callbacks else None,
                outlines,
                {
                    "prompt": state.get("outline_prompt"),
                    "raw": state.get("step_outlines_raw"),
                    "provider": state.get("outline_provider"),
                    "model": state.get("outline_model"),
                    "usage": state.get("outline_usage"),
                    "reasoning": state.get("reasoning", []),
                    "generation_method": "langgraph_episode_step_outline",
                },
            )

            provider_used = state.get("outline_provider")
            model_used = state.get("outline_model")
            usage = state.get("outline_usage")
            reasoning = list(state.get("reasoning", []))
            episodes_payload: list[Dict[str, Any]] = []
            episode_contents: list[str] = []

            for outline in outline_episodes[:episode_count]:
                ep_num = outline.get("episode_number")
                await _progress(f"生成第{ep_num}集：调用模型")
                previous_eps = [
                    {
                        "episode_number": o.get("episode_number"),
                        "title": o.get("title"),
                        "logline": o.get("logline"),
                    }
                    for o in outline_episodes
                    if o.get("episode_number")
                    and ep_num
                    and o.get("episode_number") < ep_num
                ]
                prompt = prompt_manager.render_prompt(
                    PromptTemplate.EPISODE_FROM_OUTLINE.value,
                    {
                        "story": story,
                        "outline": outline,
                        "previous_episodes": previous_eps,
                        "focus_characters": focus_characters or [],
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
                episode_obj: Dict[str, Any] | None = None
                if parsed and isinstance(parsed, dict):
                    episodes_arr = (
                        parsed.get("episodes") if "episodes" in parsed else None
                    )
                    if isinstance(episodes_arr, list) and episodes_arr:
                        episode_obj = episodes_arr[0]

                fallback_used = False
                if not episode_obj:
                    fallback_used = True
                    await _progress(f"生成第{ep_num}集：模型输出无效，使用大纲兜底")
                    episode_obj = _stub_episode_from_outline(outline)
                    reasoning.append(f"episode_parse_failed_{ep_num}")

                episode_obj.setdefault("episode_number", outline.get("episode_number"))
                await _progress(f"生成第{ep_num}集：校验中")
                try:
                    EpisodePlanItem.model_validate(episode_obj)
                    valid, reason = _is_episode_valid(episode_obj)
                    if not valid:
                        fallback_used = True
                        episode_obj = _stub_episode_from_outline(outline)
                        reasoning.append(f"episode_invalid_{ep_num}_{reason}")
                    else:
                        reasoning.append(f"episode_ok_{ep_num}")
                    episodes_payload.append(episode_obj)
                    episode_contents.append(content)
                    provider_used = resp.provider or provider_used
                    model_used = resp.model or model_used
                    usage = resp.usage or usage
                    await _maybe_await(
                        callbacks.on_episode if callbacks else None,
                        episode_obj,
                        {
                            "prompt": prompt,
                            "raw": content,
                            "provider": resp.provider,
                            "model": resp.model,
                            "usage": resp.usage,
                            "outline": outline,
                            "fallback_from_outline": fallback_used,
                        },
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
                    episode_obj = _stub_episode_from_outline(outline)
                    episodes_payload.append(episode_obj)
                    reasoning.append(f"episode_schema_invalid_{ep_num}")
                    await _maybe_await(
                        callbacks.on_episode if callbacks else None,
                        episode_obj,
                        {
                            "prompt": prompt,
                            "raw": content,
                            "provider": resp.provider,
                            "model": resp.model,
                            "usage": resp.usage,
                            "outline": outline,
                            "fallback_from_outline": True,
                            "missing_fields": missing_fields,
                        },
                    )

            return {
                "content": json.dumps(
                    {"episodes": episodes_payload}, ensure_ascii=False
                ),
                "normalized": {"episodes": episodes_payload},
                "step_outlines": outlines,
                "step_outlines_raw": state.get("step_outlines_raw"),
                "step_outline_prompt": state.get("outline_prompt"),
                "prompt": state.get("outline_prompt"),
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
