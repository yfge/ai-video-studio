from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

from app.services.continuity.episode_continuity import init_continuity_ledger_from_story
from app.services.continuity.episode_generation_flow import (
    generate_episode_with_continuity_react,
)


@dataclass(slots=True)
class EpisodeGenerationResult:
    episodes: list[Dict[str, Any]]
    provider: str | None
    model: str | None
    usage: dict | None
    reasoning: list[str]
    continuity_ledger: dict[str, Any] | None = None


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
    generation_mode: str = "standard",
) -> EpisodeGenerationResult:
    provider_used = initial_provider
    model_used = initial_model
    usage = initial_usage
    episodes_payload: list[Dict[str, Any]] = []

    outline_episodes = step_outlines.get("episodes") or []
    continuity_ledger = (
        story.get("continuity_ledger")
        if isinstance(story.get("continuity_ledger"), dict)
        else None
    )
    if not continuity_ledger:
        continuity_ledger = init_continuity_ledger_from_story(story)
    story_for_generation = dict(story or {})
    story_for_generation.update(
        {
            "generation_mode": generation_mode,
            "production_mode": generation_mode == "production",
            "episode_contract_version": "episode_contract_v1",
        }
    )

    for outline in outline_episodes[:episode_count]:
        output = await generate_episode_with_continuity_react(
            ai_manager=ai_manager,
            story=story_for_generation,
            outline=outline,
            outline_episodes=[o for o in outline_episodes if isinstance(o, dict)],
            continuity_ledger=continuity_ledger,
            episode_duration=episode_duration,
            focus_characters=focus_characters,
            plot_complexity=plot_complexity,
            pacing=pacing,
            additional_requirements=additional_requirements,
            style_preferences=style_preferences,
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
            progress=progress,
            reasoning=reasoning,
        )
        continuity_ledger = output.continuity_ledger

        episodes_payload.append(output.episode)
        provider_used = output.provider or provider_used
        model_used = output.model or model_used
        usage = output.usage or usage

        await emit_episode(
            output.episode,
            {
                "prompt": output.prompt,
                "raw": output.raw,
                "provider": output.provider,
                "model": output.model,
                "usage": output.usage,
                "outline": outline,
                "fallback_from_outline": output.fallback_from_outline,
                "react_attempts": output.react_attempts,
                "duration_accepted": output.duration_accepted,
                "continuity_snapshot": output.episode.get("continuity_snapshot"),
                "generation_mode": generation_mode,
                "production_mode": generation_mode == "production",
                "contract_version": "episode_contract_v1",
            },
        )

    return EpisodeGenerationResult(
        episodes=episodes_payload,
        provider=provider_used,
        model=model_used,
        usage=usage,
        reasoning=reasoning,
        continuity_ledger=continuity_ledger,
    )


def dumps_episode_payload(episodes: list[Dict[str, Any]]) -> str:
    return json.dumps({"episodes": episodes}, ensure_ascii=False)
