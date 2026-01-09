from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import EpisodePlanItem, EpisodePlanModel
from app.utils.json_utils import extract_json_block

from .episode_agent_episode_utils import (
    MAX_REACT_REGENERATE_ATTEMPTS,
    stub_episode_from_outline,
    validate_episode_duration,
    validate_episode_payload,
)


@dataclass(slots=True)
class EpisodeGenerationResult:
    episodes: list[Dict[str, Any]]
    provider: str | None
    model: str | None
    usage: dict | None
    reasoning: list[str]

async def generate_episodes_from_outlines(
    *,
    ai_manager: Any,
    story: Dict[str, Any],
    step_outlines: Dict[str, Any],
    episode_count: int,
    episode_duration: Optional[int],
    focus_characters: list[Dict[str, Any]],
    plot_complexity: str,
    pacing: str,
    additional_requirements: Optional[str],
    style_preferences: list[str],
    model: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
    progress: Callable[[str], Awaitable[None]],
    emit_episode: Callable[[Dict[str, Any], Dict[str, Any]], Awaitable[None]],
    reasoning: list[str],
    initial_provider: str | None,
    initial_model: str | None,
    initial_usage: dict | None,
) -> EpisodeGenerationResult:
    plan_schema = EpisodePlanModel.model_json_schema()

    provider_used = initial_provider
    model_used = initial_model
    usage = initial_usage
    episodes_payload: list[Dict[str, Any]] = []

    outline_episodes = step_outlines.get("episodes") or []
    for outline in outline_episodes[:episode_count]:
        ep_num = outline.get("episode_number") or 1
        previous_eps = [
            {
                "episode_number": o.get("episode_number"),
                "title": o.get("title"),
                "logline": o.get("logline"),
            }
            for o in outline_episodes
            if o.get("episode_number") and o.get("episode_number") < ep_num
        ]

        episode_obj: Dict[str, Any] | None = None
        content: str = ""
        fallback_used = False
        duration_accepted = False
        react_attempt = 0

        while react_attempt < MAX_REACT_REGENERATE_ATTEMPTS:
            react_attempt += 1
            is_regeneration = react_attempt > 1

            if is_regeneration and episode_obj:
                _, cur_secs, tgt_secs = validate_episode_duration(
                    episode_obj, episode_duration
                )
                rejection_reason = (
                    "duration_too_short" if cur_secs < tgt_secs else "duration_too_long"
                )
                await progress(
                    f"生成第{ep_num}集：REACT驳回（{rejection_reason}，"
                    f"{cur_secs}秒 vs 目标{tgt_secs}秒），第{react_attempt}次尝试"
                )
                reasoning.append(
                    f"episode_react_reject_{ep_num}_attempt{react_attempt - 1}_"
                    f"{rejection_reason}_{cur_secs}s"
                )
                prompt = prompt_manager.render_prompt(
                    PromptTemplate.EPISODE_DURATION_REJECT.value,
                    {
                        "story": story,
                        "outline": outline,
                        "previous_episodes": previous_eps,
                        "rejected_episode": episode_obj,
                        "target_duration_seconds": tgt_secs,
                        "current_duration_seconds": cur_secs,
                        "rejection_reason": rejection_reason,
                        "attempt_number": react_attempt,
                        "focus_characters": focus_characters,
                        "episode_duration": episode_duration,
                        "plot_complexity": plot_complexity,
                        "pacing": pacing,
                    },
                )
            else:
                await progress(f"生成第{ep_num}集：调用模型")
                prompt = prompt_manager.render_prompt(
                    PromptTemplate.EPISODE_FROM_OUTLINE.value,
                    {
                        "story": story,
                        "outline": outline,
                        "previous_episodes": previous_eps,
                        "focus_characters": focus_characters,
                        "episode_duration": episode_duration,
                        "plot_complexity": plot_complexity,
                        "pacing": pacing,
                        "additional_requirements": additional_requirements,
                        "style_preferences": style_preferences,
                    },
                )

            resp = await ai_manager.generate_text(
                prompt=prompt,
                temperature=temperature,
                model=model,
                prefer_provider=prefer_provider,
                json_schema={"name": "episode_plan", "schema": plan_schema},
                system_prompt=prompt_manager.render_prompt(
                    PromptTemplate.SYSTEM_PROMPT_SCRIPT.value,
                    {"story_format": story.get("story_format")},
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
                fallback_used = True
                await progress(f"生成第{ep_num}集：模型输出无效，使用大纲兜底")
                episode_obj = stub_episode_from_outline(outline)
                reasoning.append(f"episode_parse_failed_{ep_num}")
                break

            episode_obj.setdefault("episode_number", outline.get("episode_number"))
            await progress(f"生成第{ep_num}集：校验中")

            try:
                EpisodePlanItem.model_validate(episode_obj)
                valid, reason = validate_episode_payload(episode_obj)
                if not valid:
                    fallback_used = True
                    episode_obj = stub_episode_from_outline(outline)
                    reasoning.append(f"episode_invalid_{ep_num}_{reason}")
                    break
            except Exception:
                fallback_used = True
                episode_obj = stub_episode_from_outline(outline)
                reasoning.append(f"episode_schema_invalid_{ep_num}")
                break

            if episode_duration:
                dur_valid, cur_secs, _ = validate_episode_duration(
                    episode_obj, episode_duration
                )
                if dur_valid:
                    duration_accepted = True
                    reasoning.append(
                        f"episode_duration_ok_{ep_num}_attempt{react_attempt}_{cur_secs}s"
                    )
                    await progress(f"生成第{ep_num}集：时长验证通过（{cur_secs}秒）")
                    break

                reasoning.append(
                    f"episode_duration_bad_{ep_num}_attempt{react_attempt}_{cur_secs}s"
                )
                if react_attempt >= MAX_REACT_REGENERATE_ATTEMPTS:
                    reasoning.append(
                        f"episode_duration_accepted_after_max_attempts_{ep_num}_{cur_secs}s"
                    )
                    await progress(
                        f"生成第{ep_num}集：达到最大重试次数，接受当前时长（{cur_secs}秒）"
                    )
                    break
                continue

            reasoning.append(f"episode_ok_{ep_num}")
            break

        if not episode_obj:
            continue

        episodes_payload.append(episode_obj)
        provider_used = resp.provider or provider_used
        model_used = resp.model or model_used
        usage = resp.usage or usage

        await emit_episode(
            episode_obj,
            {
                "prompt": prompt,
                "raw": content,
                "provider": resp.provider,
                "model": resp.model,
                "usage": resp.usage,
                "outline": outline,
                "fallback_from_outline": fallback_used,
                "react_attempts": react_attempt,
                "duration_accepted": duration_accepted,
            },
        )

    return EpisodeGenerationResult(
        episodes=episodes_payload,
        provider=provider_used,
        model=model_used,
        usage=usage,
        reasoning=reasoning,
    )


def dumps_episode_payload(episodes: list[Dict[str, Any]]) -> str:
    return json.dumps({"episodes": episodes}, ensure_ascii=False)
