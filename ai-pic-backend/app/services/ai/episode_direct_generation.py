from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import EpisodePlanModel
from app.services.ai.structured_output import generate_with_repair
from app.services.continuity.episode_plan_postprocess import (
    postprocess_episode_plan_list,
)


async def call_ai_manager_episode(
    *,
    ai_manager: Any,
    story: Dict[str, Any],
    episode_count: int,
    episode_duration: Optional[int],
    focus_characters: Optional[List[Dict[str, Any]]],
    plot_complexity: str,
    pacing: str,
    additional_requirements: Optional[str],
    style_preferences: Optional[List[str]],
    model: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
    generation_mode: str = "standard",
) -> Optional[Dict[str, Any]]:
    production_mode = generation_mode == "production"
    variables = {
        "story": story,
        "episode_count": episode_count,
        "episode_duration": episode_duration,
        "focus_characters": focus_characters or [],
        "plot_complexity": plot_complexity,
        "pacing": pacing,
        "additional_requirements": additional_requirements,
        "style_preferences": style_preferences or [],
        "generation_mode": generation_mode,
        "production_mode": production_mode,
        "episode_contract_version": "episode_contract_v1",
    }
    prompt = prompt_manager.render_prompt(
        PromptTemplate.EPISODE_GENERATION.value,
        variables,
    )
    plan_schema = EpisodePlanModel.model_json_schema()
    episodes_schema = plan_schema.get("properties", {}).get("episodes")
    if isinstance(episodes_schema, dict):
        episodes_schema["minItems"] = episode_count
        episodes_schema["maxItems"] = episode_count

    def _extra_validator(payload: Dict[str, Any]):
        episodes = payload.get("episodes")
        if not isinstance(episodes, list):
            return [
                {
                    "loc": ["episodes"],
                    "msg": "episodes must be a list",
                    "type": "value_error.episodes_type",
                }
            ]
        if len(episodes) != episode_count:
            return [
                {
                    "loc": ["episodes"],
                    "msg": f"expected {episode_count} episodes, got {len(episodes)}",
                    "type": "value_error.episode_count_mismatch",
                }
            ]
        return None

    strict_json_prompt = prompt_manager.render_prompt(
        PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
    )
    output = await generate_with_repair(
        ai_manager=ai_manager,
        base_prompt=prompt,
        temperature=temperature,
        model=model,
        prefer_provider=prefer_provider,
        schema_name="episode_plan",
        schema=plan_schema,
        system_prompt=strict_json_prompt,
        repair_system_prompt=strict_json_prompt,
        pydantic_model=EpisodePlanModel,
        extractor=None,
        extra_validator=_extra_validator,
        max_repairs=2,
    )
    normalized = output.get("normalized")
    if not isinstance(normalized, dict) or not normalized.get("episodes"):
        return None
    episodes = normalized.get("episodes")
    updated, ledger, rewritten_text = await postprocess_episode_plan_list(
        ai_manager=ai_manager,
        story=story,
        episodes=episodes,
        model=model,
        prefer_provider=prefer_provider,
        temperature=temperature,
    )
    normalized["episodes"] = updated

    first_attempt = output.get("first_attempt") or {}
    repair_attempts = output.get("repair_attempts") or []
    last_meta = (
        (repair_attempts[-1] if repair_attempts else first_attempt)
        if isinstance(first_attempt, dict)
        else {}
    )
    provider_used = last_meta.get("provider_used")
    model_used = last_meta.get("model_used")
    usage = last_meta.get("usage")

    return {
        "content": rewritten_text or output.get("content") or "",
        "normalized": normalized,
        "validation_errors": output.get("validation_errors"),
        "repair_attempts": repair_attempts,
        "first_attempt": first_attempt,
        "prompt": prompt,
        "generation_method": f"ai_{provider_used}",
        "template_used": PromptTemplate.EPISODE_GENERATION.value,
        "continuity_ledger": ledger,
        "provider_used": provider_used,
        "model_used": model_used,
        "usage": usage,
        "generation_mode": generation_mode,
        "production_mode": production_mode,
        "prompt_version": PromptTemplate.EPISODE_GENERATION.value,
        "contract_version": "episode_contract_v1",
    }


def build_episode_generation_prompt(
    story: Dict[str, Any],
    episode_count: int,
    episode_duration: Optional[int] = None,
    focus_characters: Optional[List[Dict[str, Any]]] = None,
    plot_complexity: str = "medium",
    pacing: str = "medium",
    additional_requirements: Optional[str] = None,
    style_preferences: Optional[List[str]] = None,
) -> str:
    characters_desc = ""
    if focus_characters:
        characters_desc = "重点角色:\n"
        for char in focus_characters:
            characters_desc += (
                f"- {char.get('name', '未知角色')}: "
                f"{char.get('description', '无描述')}\n"
            )
    return f"""
你是一名专业的剧本创作AI助手。请根据以下故事概要生成 {episode_count} 集的剧集规划。

故事概要:
标题: {story.get('title', '')}
类型: {story.get('genre', '')}
目标市场: {story.get('market_region', '')}
微类型: {story.get('micro_genre', '')}
主题: {story.get('theme', '')}
简介: {story.get('synopsis', '')}
主要冲突: {story.get('main_conflict', '')}
结局: {story.get('resolution', '')}
爽点规划: {story.get('hook_plan', '')}
反转密度: {story.get('twist_density', '')}
悬念卡点: {story.get('cliffhanger_plan', '')}
投流素材: {story.get('ad_snippets', '')}

{characters_desc}

要求:
1. 每集时长约 {episode_duration} 分钟
2. 剧情复杂度: {plot_complexity}
3. 节奏: {pacing}
4. 其他要求: {additional_requirements or '无'}
5. 风格偏好: {', '.join(style_preferences) if style_preferences else '无'}

请为每一集提供标题、概要、主要剧情点、角色发展和冲突。
"""
