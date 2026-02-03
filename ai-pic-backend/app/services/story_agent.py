from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.prompts.manager import prompt_manager
from app.prompts.template_resolver import resolve_template_name
from app.prompts.templates import PromptTemplate
from app.schemas.generation import StoryOutlineModel
from app.services.validators.character_consistency_validator import (
    CharacterConsistencyValidator,
    CharacterProfile,
)
from app.utils.json_utils import extract_json_block

logger = logging.getLogger(__name__)

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
        self._character_validator = CharacterConsistencyValidator()

    def _build_character_profiles(
        self, characters: List[Dict[str, Any]]
    ) -> List[CharacterProfile]:
        """Convert input character dicts to CharacterProfile objects."""
        profiles = []
        for char in characters:
            if not char.get("name"):
                continue
            profile = CharacterProfile(
                name=char.get("name", ""),
                aliases=char.get("aliases", []),
                role_type=char.get("role_type") or char.get("role"),
                gender=char.get("gender"),
                age=char.get("age"),
                personality=char.get("personality", []),
                appearance=char.get("appearance") or char.get("description"),
            )
            profiles.append(profile)
        return profiles

    def _validate_story_characters(
        self,
        parsed: Dict[str, Any],
        input_characters: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate that generated story characters are consistent with input.

        Returns validation results dict with:
        - character_validation_passed: bool
        - character_validation_results: list of validation results
        - character_warnings: list of warning messages
        """
        results: Dict[str, Any] = {
            "character_validation_passed": True,
            "character_validation_results": [],
            "character_warnings": [],
        }

        # Build profiles from input characters
        profiles = self._build_character_profiles(input_characters)
        if not profiles:
            results["character_warnings"].append("No input characters to validate against")
            return results

        self._character_validator = CharacterConsistencyValidator()
        self._character_validator.register_profiles(profiles)

        # Extract characters from generated story
        story_characters = parsed.get("characters", [])
        if isinstance(story_characters, list):
            for char in story_characters:
                if isinstance(char, dict):
                    name = char.get("name") or char.get("character_name")
                    if not name:
                        continue

                    # Check if character exists in input
                    canonical = self._character_validator.resolve_name(name)
                    if not canonical:
                        results["character_warnings"].append(
                            f"Generated character '{name}' not found in input characters"
                        )
                        results["character_validation_passed"] = False
                        continue

                    # Validate attributes
                    attrs = {}
                    if char.get("gender"):
                        attrs["gender"] = char["gender"]
                    if char.get("age"):
                        attrs["age"] = char["age"]
                    if char.get("personality"):
                        attrs["personality"] = char["personality"]

                    if attrs:
                        attr_results = self._character_validator.validate_character_attributes(
                            name, attrs
                        )
                        for r in attr_results:
                            results["character_validation_results"].append(r.to_dict())
                            if not r.passed:
                                results["character_validation_passed"] = False
                                results["character_warnings"].append(r.message)

        # Also validate any character names in premise/synopsis
        content_to_check = []
        if parsed.get("premise"):
            content_to_check.append(parsed["premise"])
        if parsed.get("synopsis"):
            content_to_check.append(parsed["synopsis"])

        if content_to_check:
            text_results = self._character_validator.validate_names_in_text(
                "\n".join(content_to_check)
            )
            for r in text_results:
                results["character_validation_results"].append(r.to_dict())
                if r.severity.value == "warning":
                    results["character_warnings"].append(r.message)

        return results

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

        try:
            if parsed:
                StoryOutlineModel.model_validate(parsed)
                # Run character consistency validation
                char_validation = self._validate_story_characters(parsed, characters)
                if char_validation["character_warnings"]:
                    logger.warning(
                        "Story character validation warnings",
                        extra={"warnings": char_validation["character_warnings"]},
                    )
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
                    **char_validation,
                }
        except Exception:
            pass

        missing_fields: list[str] = []
        for attempt in range(3):
            if parsed:
                try:
                    StoryOutlineModel.model_validate(parsed)
                    # Run character consistency validation
                    char_validation = self._validate_story_characters(parsed, characters)
                    if char_validation["character_warnings"]:
                        logger.warning(
                            "Story character validation warnings (repair attempt)",
                            extra={"warnings": char_validation["character_warnings"]},
                        )
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
                        **char_validation,
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
