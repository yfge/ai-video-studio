from __future__ import annotations

import json
import logging
from importlib.util import find_spec
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.prompts.manager import prompt_manager
from app.prompts.template_resolver import resolve_template_name
from app.prompts.templates import PromptTemplate
from app.services.story_agent_validation import (
    build_story_agent_result,
    story_outline_schema,
    validate_story_outline_candidate,
)
from app.utils.json_utils import extract_json_block

logger = logging.getLogger(__name__)

LANGGRAPH_AVAILABLE = find_spec("langgraph") is not None

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
    text = (
        payload
        if isinstance(payload, str)
        else ("" if payload is None else str(payload))
    )
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
        pacing_template: Optional[str] = None,
        hook_plan: Optional[Dict[str, Any]] = None,
        twist_density: Optional[str] = None,
        cliffhanger_plan: Optional[List[str]] = None,
        ad_snippets: Optional[List[Dict[str, Any]]] = None,
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
        generation_mode: str = "standard",
    ) -> Optional[Dict[str, Any]]:
        if not LANGGRAPH_AVAILABLE or not getattr(self.service, "ai_manager", None):
            return None

        production_mode = generation_mode == "production"
        schema = story_outline_schema(production_mode=production_mode)
        variables = {
            "title": title,
            "story_format": story_format,
            "genre": genre,
            "characters": characters,
            "market_region": market_region,
            "micro_genre": micro_genre,
            "pacing_template": pacing_template,
            "hook_plan": hook_plan,
            "twist_density": twist_density,
            "cliffhanger_plan": cliffhanger_plan or [],
            "ad_snippets": ad_snippets or [],
            "theme": theme,
            "target_audience": target_audience,
            "duration_minutes": duration_minutes,
            "setting_time": setting_time,
            "setting_location": setting_location,
            "world_building": world_building,
            "additional_requirements": additional_requirements,
            "style_preferences": style_preferences or [],
            "content_restrictions": content_restrictions or [],
            "generation_mode": generation_mode,
            "production_mode": production_mode,
            "story_contract_version": "story_contract_v1",
        }
        resolved_template = resolve_template_name(
            PromptTemplate.STORY_OUTLINE.value, variables, prompt_manager.prompts_dir
        )
        prompt = prompt_manager.render_prompt(
            PromptTemplate.STORY_OUTLINE.value, variables
        )
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
        quality_gate_issues: list[str] = []
        quality_gate_issue_details: list[str] = []
        story_quality_warnings: list[str] = []
        character_warnings: list[str] = []

        try:
            if parsed:
                validation = validate_story_outline_candidate(
                    parsed,
                    characters=characters,
                    hook_plan=hook_plan,
                    content_restrictions=content_restrictions,
                    production_mode=production_mode,
                    log_suffix="",
                )
                character_warnings = validation.character_warnings
                story_quality_warnings = validation.story_quality_warnings
                quality_gate_issues = validation.quality_gate_issues
                quality_gate_issue_details = validation.quality_gate_issue_details
                if validation.passed:
                    return build_story_agent_result(
                        latest_text=latest_text,
                        parsed=parsed,
                        resolved_template=resolved_template,
                        provider_used=provider_used,
                        model_used=model_used,
                        usage=usage,
                        prompt=prompt,
                        generation_mode=generation_mode,
                        production_mode=production_mode,
                        reasoning=reasoning + ["validated"],
                        validation=validation,
                    )
        except Exception:
            pass

        missing_fields: list[str] = []
        for attempt in range(3):
            if parsed:
                try:
                    validation = validate_story_outline_candidate(
                        parsed,
                        characters=characters,
                        hook_plan=hook_plan,
                        content_restrictions=content_restrictions,
                        production_mode=production_mode,
                        log_suffix=" (repair attempt)",
                    )
                    character_warnings = validation.character_warnings
                    story_quality_warnings = validation.story_quality_warnings
                    quality_gate_issues = validation.quality_gate_issues
                    quality_gate_issue_details = validation.quality_gate_issue_details
                    if validation.passed:
                        return build_story_agent_result(
                            latest_text=latest_text,
                            parsed=parsed,
                            resolved_template=resolved_template,
                            provider_used=provider_used,
                            model_used=model_used,
                            usage=usage,
                            prompt=prompt,
                            generation_mode=generation_mode,
                            production_mode=production_mode,
                            reasoning=reasoning + [f"validated_attempt_{attempt}"],
                            validation=validation,
                        )
                except Exception as exc:  # pragma: no cover - schema guard
                    missing_fields = _extract_missing_fields(exc)

            repair_prompt = prompt_manager.render_prompt(
                PromptTemplate.STORY_OUTLINE_REPAIR.value,
                {
                    "schema": schema,
                    "original_prompt": prompt,
                    "original_output": latest_text,
                    "missing_fields": missing_fields,
                    "production_mode": production_mode,
                    "story_contract_version": "story_contract_v1",
                    "quality_gate_issues": quality_gate_issues,
                    "quality_gate_issue_details": quality_gate_issue_details,
                    "story_quality_warnings": story_quality_warnings,
                    "character_warnings": character_warnings,
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
