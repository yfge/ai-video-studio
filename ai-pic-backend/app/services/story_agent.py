from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.prompts.manager import prompt_manager
from app.prompts.template_resolver import resolve_template_name
from app.prompts.templates import PromptTemplate
from app.schemas.generation import StoryOutlineModel
from app.utils.json_utils import extract_json_block

try:  # pragma: no cover - optional dependency
    import langgraph  # noqa: F401

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    LANGGRAPH_AVAILABLE = False

if TYPE_CHECKING:
    from .ai_service import AIService


def _extract_missing_fields(exc: Exception) -> list[str]:
    try:
        return ["/".join(map(str, err.get("loc", []))) for err in exc.errors()]
    except Exception:
        return []


def _coerce_text_and_parsed(payload: object) -> tuple[str, dict | None]:
    if isinstance(payload, dict):
        return json.dumps(payload, ensure_ascii=False), payload
    text = payload if isinstance(payload, str) else ("" if payload is None else str(payload))
    return text, extract_json_block(text)


class StoryLangGraphAgent:
    """Story outline generator with schema validation + repair loop."""

    def __init__(self, service: "AIService") -> None:
        self.service = service

    async def generate(
        self,
        *,
        title: str,
        story_format: Optional[str],
        genre: str,
        characters: List[Dict[str, Any]],
        market_region: Optional[str],
        micro_genre: Optional[str],
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
        if not LANGGRAPH_AVAILABLE or not getattr(self.service, "ai_manager", None):
            return None

        schema = StoryOutlineModel.model_json_schema()
        variables = {
            "title": title,
            "story_format": story_format,
            "genre": genre,
            "characters": characters,
            "market_region": market_region,
            "micro_genre": micro_genre,
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
        resolved_template = resolve_template_name(
            PromptTemplate.STORY_OUTLINE.value, variables, prompt_manager.prompts_dir
        )
        prompt = prompt_manager.render_prompt(PromptTemplate.STORY_OUTLINE.value, variables)
        system_prompt = (
            prompt_manager.render_prompt(
                PromptTemplate.SYSTEM_PROMPT_STORY.value,
                {"story_format": story_format},
            )
            + " 并严格输出 JSON。"
        )

        resp = await self.service.ai_manager.generate_text(
            prompt=prompt,
            temperature=temperature,
            model=model,
            prefer_provider=prefer_provider,
            json_schema={"name": "story_outline", "schema": schema},
            system_prompt=system_prompt,
        )
        latest_text, parsed = _coerce_text_and_parsed(resp.data)
        provider_used = resp.provider
        model_used = resp.model
        usage = resp.usage
        reasoning = ["draft_ok"] if resp.success else ["draft_failed"]

        try:
            if parsed:
                StoryOutlineModel.model_validate(parsed)
                return {
                    "content": latest_text,
                    "normalized": parsed,
                    "generation_method": "langgraph_story",
                    "template_used": resolved_template,
                    "provider_used": provider_used,
                    "model_used": model_used,
                    "usage": usage,
                    "prompt": prompt,
                    "reasoning": reasoning + ["validated"],
                }
        except Exception:
            pass

        missing_fields: list[str] = []
        for attempt in range(3):
            if parsed:
                try:
                    StoryOutlineModel.model_validate(parsed)
                    return {
                        "content": latest_text,
                        "normalized": parsed,
                        "generation_method": "langgraph_story",
                        "template_used": resolved_template,
                        "provider_used": provider_used,
                        "model_used": model_used,
                        "usage": usage,
                        "prompt": prompt,
                        "reasoning": reasoning + [f"validated_attempt_{attempt}"],
                    }
                except Exception as exc:  # pragma: no cover - schema guard
                    missing_fields = _extract_missing_fields(exc)

            repair_prompt = prompt_manager.render_prompt(
                PromptTemplate.STORY_OUTLINE_REPAIR.value,
                {
                    "schema": schema,
                    "original_prompt": prompt,
                    "original_output": latest_text,
                    "missing_fields": missing_fields,
                },
            )
            repair_resp = await self.service.ai_manager.generate_text(
                prompt=repair_prompt,
                temperature=temperature,
                model=model,
                prefer_provider=prefer_provider,
                json_schema={"name": "story_outline_repair", "schema": schema},
                system_prompt=prompt_manager.render_prompt(
                    PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
                ),
            )
            latest_text, parsed = _coerce_text_and_parsed(repair_resp.data)
            provider_used = repair_resp.provider or provider_used
            model_used = repair_resp.model or model_used
            usage = repair_resp.usage or usage
            reasoning.append(f"repair_attempt_{attempt + 1}")

        return None
