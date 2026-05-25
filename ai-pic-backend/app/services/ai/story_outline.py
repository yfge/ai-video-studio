from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.prompts.manager import prompt_manager
from app.prompts.template_resolver import resolve_template_name
from app.prompts.templates import PromptTemplate
from app.schemas.generation import StoryOutlineModel
from app.services.ai.structured_output import generate_with_repair, validate_payload
from app.utils.story_parser import extract_story_outline_payload


def story_outline_fallback_generation_method(normalized: Any) -> str:
    return "ai_fallback" if normalized else "ai_fallback_invalid"


class StoryOutlineMixin:
    async def generate_story_outline(
        self,
        title: str,
        genre: str,
        characters: List[Dict[str, Any]],
        story_format: Optional[str] = None,
        market_region: Optional[str] = None,
        micro_genre: Optional[str] = None,
        pacing_template: Optional[str] = None,
        hook_plan: Optional[Dict[str, Any]] = None,
        twist_density: Optional[str] = None,
        cliffhanger_plan: Optional[List[str]] = None,
        ad_snippets: Optional[List[Dict[str, Any]]] = None,
        theme: Optional[str] = None,
        target_audience: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        setting_time: Optional[str] = None,
        setting_location: Optional[str] = None,
        world_building: Optional[str] = None,
        additional_requirements: Optional[str] = None,
        style_preferences: Optional[List[str]] = None,
        content_restrictions: Optional[List[str]] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        prefer_provider: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """生成故事概要"""

        try:

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

            story_schema = StoryOutlineModel.model_json_schema()

            if self.story_agent:
                lg = await self.story_agent.generate(
                    title=title,
                    story_format=story_format,
                    genre=genre,
                    characters=characters,
                    market_region=market_region,
                    micro_genre=micro_genre,
                    pacing_template=pacing_template,
                    hook_plan=hook_plan,
                    twist_density=twist_density,
                    cliffhanger_plan=cliffhanger_plan,
                    ad_snippets=ad_snippets,
                    theme=theme,
                    target_audience=target_audience,
                    duration_minutes=duration_minutes,
                    setting_time=setting_time,
                    setting_location=setting_location,
                    world_building=world_building,
                    additional_requirements=additional_requirements,
                    style_preferences=style_preferences,
                    content_restrictions=content_restrictions,
                    model=model,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                )
                if lg:
                    return lg

            resolved_template = resolve_template_name(
                PromptTemplate.STORY_OUTLINE.value,
                variables,
                prompt_manager.prompts_dir,
            )
            prompt = prompt_manager.render_prompt(
                PromptTemplate.STORY_OUTLINE.value, variables
            )

            # 优先使用新的AI服务管理器；如果失败则尝试兜底。
            if self.ai_manager:
                try:
                    system_prompt = prompt_manager.render_prompt(
                        PromptTemplate.SYSTEM_PROMPT_STORY.value,
                        {"story_format": story_format},
                    )
                    strict_system_prompt = prompt_manager.render_prompt(
                        PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
                    )

                    output = await generate_with_repair(
                        ai_manager=self.ai_manager,
                        base_prompt=prompt,
                        temperature=temperature,
                        model=model,
                        prefer_provider=prefer_provider,
                        schema_name="story_outline",
                        schema=story_schema,
                        system_prompt=system_prompt,
                        repair_system_prompt=strict_system_prompt,
                        pydantic_model=StoryOutlineModel,
                        extractor=extract_story_outline_payload,
                        max_repairs=2,
                    )

                    content_text = output.get("content") or ""
                    normalized = output.get("normalized")
                    validation_errors = output.get("validation_errors")
                    repair_attempts = output.get("repair_attempts") or []
                    first_attempt = output.get("first_attempt") or {}

                    last_meta = (
                        (repair_attempts[-1] if repair_attempts else first_attempt)
                        if isinstance(first_attempt, dict)
                        else {}
                    )
                    provider_used = last_meta.get("provider_used")
                    model_used = last_meta.get("model_used")
                    usage = last_meta.get("usage")

                    if content_text:
                        generation_suffix = "" if normalized else "_invalid"
                        return {
                            "content": content_text,
                            "normalized": normalized,
                            "validation_errors": validation_errors,
                            "repair_attempts": repair_attempts,
                            "first_attempt": first_attempt,
                            "prompt": prompt,
                            "generation_method": f"ai_{provider_used}{generation_suffix}",
                            "template_used": resolved_template,
                            "provider_used": provider_used,
                            "model_used": model_used,
                            "usage": usage,
                        }
                except Exception as exc:
                    self.logger.warning(f"AI服务管理器故事生成失败，尝试回退: {exc}")

            # 兜底：使用文本生成服务链（最终会回退到 mock）；若用户显式指定 provider/model，则直接失败，避免“扯淡”内容落库。
            if prefer_provider or model:
                self.logger.warning(
                    "Story outline generation failed for explicit provider/model; skip mock fallback",
                    extra={
                        "prefer_provider": prefer_provider,
                        "model": model,
                        "story_format": story_format,
                    },
                )
                return None

            fallback_content = await self._call_text_generation_service(
                prompt, "story_outline", story_format=story_format
            )
            if fallback_content:
                normalized, validation_errors, _raw_json = validate_payload(
                    StoryOutlineModel,
                    fallback_content,
                    extractor=extract_story_outline_payload,
                )
                return {
                    "content": fallback_content,
                    "normalized": normalized,
                    "validation_errors": validation_errors,
                    "prompt": prompt,
                    "generation_method": story_outline_fallback_generation_method(
                        normalized
                    ),
                    "template_used": resolved_template,
                    "provider_used": "fallback",
                    "model_used": "mock",
                    "usage": {},
                }
        except Exception as exc:
            print(f"故事概要生成失败: {exc}")

        return None
