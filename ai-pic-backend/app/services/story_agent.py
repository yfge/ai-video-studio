from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.core.logging import get_logger
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import StoryOutlineModel
from app.utils.json_utils import extract_json_block

try:
    from langgraph.graph import StateGraph, END

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    LANGGRAPH_AVAILABLE = False

if TYPE_CHECKING:
    from .ai_service import AIService


class StoryLangGraphAgent:
    """LangGraph pipeline for story outline generation using prompt templates."""

    def __init__(self, service: "AIService") -> None:
        self.service = service
        self.logger = get_logger()

    async def generate(
        self,
        *,
        title: str,
        genre: str,
        characters: List[Dict[str, Any]],
        theme: Optional[str],
        target_audience: Optional[str],
        duration_minutes: Optional[int],
        setting_time: Optional[str],
        setting_location: Optional[str],
        world_building: Optional[str],
        additional_requirements: Optional[str],
        style_preferences: Optional[List[str]],
        content_restrictions: Optional[List[str]],
        model: Optional[str],
        prefer_provider: Optional[str],
        temperature: float,
    ) -> Optional[Dict[str, Any]]:
        if not LANGGRAPH_AVAILABLE or not self.service.ai_manager:
            return None

        schema = StoryOutlineModel.model_json_schema()

        def _extract_missing_fields(exc: Exception) -> list[str]:
            try:
                return ["/".join(map(str, err.get("loc", []))) for err in exc.errors()]
            except Exception:
                return []

        variables = {
            "title": title,
            "genre": genre,
            "characters": characters,
            "theme": theme,
            "target_audience": target_audience,
            "duration_minutes": duration_minutes,
            "setting_time": setting_time,
            "setting_location": setting_location,
            "world_building": world_building,
            "additional_requirements": additional_requirements,
            "style_preferences": style_preferences or [],
            "content_restrictions": content_restrictions or [],
        }
        story_schema = StoryOutlineModel.model_json_schema()

        graph = StateGraph(dict)

        async def draft(state: Dict[str, Any]) -> Dict[str, Any]:
            prompt = prompt_manager.render_prompt(
                PromptTemplate.STORY_OUTLINE.value, variables
            )
            resp = await self.service.ai_manager.generate_text(
                prompt=prompt,
                temperature=temperature,
                model=model,
                prefer_provider=prefer_provider,
                json_schema={"name": "story_outline", "schema": story_schema},
                system_prompt="你是一个专业的编剧和故事创作者，擅长创作各种类型的短剧剧本。请根据用户的要求生成高质量的故事内容，并严格输出 JSON。",
            )
            content = (
                resp.data
                if isinstance(resp.data, str)
                else ("" if resp.data is None else str(resp.data))
            )
            state_update = {
                "prompt": prompt,
                "content": content,
                "provider": resp.provider,
                "model_used": resp.model,
                "usage": resp.usage,
                "reasoning": ["draft_ok"] if resp.success else ["draft_failed"],
            }
            if not resp.success:
                state_update["error"] = "draft_failed"
            return state_update

        def validate(state: Dict[str, Any]) -> Dict[str, Any]:
            """Initial parse + schema validation; hand off to repair if invalid."""
            content_text = state.get("content") or ""
            reasoning = list(state.get("reasoning", []))
            parsed = (
                extract_json_block(content_text)
                if isinstance(content_text, str)
                else (content_text if isinstance(content_text, dict) else None)
            )
            if not parsed:
                reasoning.append("parse_failed")
                return {
                    "needs_repair": True,
                    "raw": content_text,
                    "reasoning": reasoning,
                }
            try:
                StoryOutlineModel.model_validate(parsed)
                reasoning.append("validated")
                return {
                    "content": content_text,
                    "normalized": parsed,
                    "generation_method": "langgraph_story",
                    "template_used": PromptTemplate.STORY_OUTLINE.value,
                    "provider_used": state.get("provider"),
                    "model_used": state.get("model_used"),
                    "usage": state.get("usage"),
                    "prompt": state.get("prompt"),
                    "reasoning": reasoning,
                }
            except Exception as exc:  # pragma: no cover - schema guard
                missing_fields = _extract_missing_fields(exc)
                reasoning.append("schema_invalid")
                return {
                    "needs_repair": True,
                    "raw": content_text,
                    "missing_fields": missing_fields,
                    "reasoning": reasoning,
                    "prompt": state.get("prompt"),
                    "provider": state.get("provider"),
                    "model_used": state.get("model_used"),
                    "usage": state.get("usage"),
                }

        async def repair(state: Dict[str, Any]) -> Dict[str, Any]:
            """Repair loop with up to 3 attempts; uses prompt_manager repair template."""
            if state.get("normalized") and not state.get("needs_repair"):
                state.setdefault("reasoning", []).append("repair_skip_validated")
                return state

            latest_text = state.get("raw") or state.get("content") or ""
            reasoning = list(state.get("reasoning", []))
            provider_used = state.get("provider_used") or state.get("provider")
            model_used = state.get("model_used")
            usage = state.get("usage")
            missing_fields = state.get("missing_fields") or []

            for attempt in range(3):
                parsed = (
                    extract_json_block(latest_text)
                    if isinstance(latest_text, str)
                    else (latest_text if isinstance(latest_text, dict) else None)
                )
                if parsed:
                    try:
                        StoryOutlineModel.model_validate(parsed)
                        reasoning.append(f"validated_attempt_{attempt}")
                        return {
                            "content": latest_text,
                            "normalized": parsed,
                            "generation_method": "langgraph_story",
                            "template_used": PromptTemplate.STORY_OUTLINE.value,
                            "provider_used": provider_used,
                            "model_used": model_used,
                            "usage": usage,
                            "prompt": state.get("prompt"),
                            "reasoning": reasoning + ["validated"],
                        }
                    except Exception as exc:  # pragma: no cover - schema guard
                        missing_fields = _extract_missing_fields(exc)
                        reasoning.append(f"schema_invalid_attempt_{attempt}")
                        self.logger.info(
                            "Story validation failed; repairing",
                            extra={"attempt": attempt, "missing": missing_fields},
                        )
                else:
                    reasoning.append(f"parse_failed_attempt_{attempt}")
                    self.logger.info(
                        "Story parse failed; repairing", extra={"attempt": attempt}
                    )

                if attempt >= 2:
                    break

                repair_prompt = prompt_manager.render_prompt(
                    PromptTemplate.STORY_OUTLINE_REPAIR.value,
                    {
                        "schema": schema,
                        "original_prompt": state.get("prompt"),
                        "original_output": latest_text,
                        "missing_fields": missing_fields if parsed else [],
                    },
                )
                resp = await self.service.ai_manager.generate_text(
                    prompt=repair_prompt,
                    temperature=temperature,
                    model=model,
                    prefer_provider=prefer_provider,
                    json_schema={"name": "story_outline_repair", "schema": schema},
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
                "error": "schema_invalid",
                "raw": latest_text,
                "reasoning": reasoning + ["schema_invalid"],
            }

        graph.add_node("draft", draft)
        graph.add_node("validate", validate)
        graph.add_node("repair", repair)
        graph.add_edge("draft", "validate")
        graph.add_edge("validate", "repair")
        graph.add_edge("repair", END)
        graph.set_entry_point("draft")

        app = graph.compile()
        result = await app.ainvoke({})

        if result.get("error") or not result.get("normalized"):
            self.logger.warning(
                "LangGraph story agent failed, falling back to default",
                extra={
                    "error": result.get("error"),
                    "reasoning": result.get("reasoning"),
                },
            )
            return None

        return result
