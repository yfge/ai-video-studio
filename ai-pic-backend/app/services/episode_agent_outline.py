from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import EpisodeStepOutlineModel
from app.utils.json_utils import extract_json_block


@dataclass(slots=True)
class OutlineGenerationResult:
    step_outlines: dict[str, Any] | None
    raw_text: str
    prompt: str
    provider: str | None
    model: str | None
    usage: dict | None
    reasoning: list[str]
    error: str | None = None


def _extract_missing_fields(exc: Exception) -> list[str]:
    try:
        return ["/".join(map(str, err.get("loc", []))) for err in exc.errors()]
    except Exception:
        return []


def _normalize_outline_episodes(outlines: dict) -> dict:
    episodes = outlines.get("episodes") if isinstance(outlines, dict) else None
    if not isinstance(episodes, list):
        return {"episodes": []}

    normalized = sorted(
        [item for item in episodes if isinstance(item, dict)],
        key=lambda x: x.get("episode_number") or 0,
    )
    for idx, item in enumerate(normalized, start=1):
        item.setdefault("episode_number", idx)
        beats = item.get("beats")
        if isinstance(beats, list):
            for b_idx, beat in enumerate(beats, start=1):
                if isinstance(beat, dict):
                    beat.setdefault("sequence_number", b_idx)
            item["beats"] = beats
    outlines["episodes"] = normalized
    return outlines


async def generate_step_outlines(
    *,
    ai_manager: Any,
    story: dict[str, Any],
    episode_count: int,
    episode_duration: Optional[int],
    focus_characters: list[dict[str, Any]],
    plot_complexity: str,
    pacing: str,
    additional_requirements: Optional[str],
    style_preferences: list[str],
    model: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
    progress: Callable[[str], Awaitable[None]],
    generation_mode: str = "standard",
) -> OutlineGenerationResult:
    outline_schema = EpisodeStepOutlineModel.model_json_schema()
    production_mode = generation_mode == "production"

    outline_variables = {
        "story": story,
        "episode_count": episode_count,
        "episode_duration": episode_duration,
        "focus_characters": focus_characters,
        "plot_complexity": plot_complexity,
        "pacing": pacing,
        "additional_requirements": additional_requirements,
        "style_preferences": style_preferences,
        "generation_mode": generation_mode,
        "production_mode": production_mode,
        "episode_contract_version": "episode_contract_v1",
    }

    await progress("剧集大纲：调用模型")
    outline_prompt = prompt_manager.render_prompt(
        PromptTemplate.EPISODE_STEP_OUTLINE.value, outline_variables
    )
    outline_resp = await ai_manager.generate_text(
        prompt=outline_prompt,
        temperature=min(0.6, temperature),
        model=model,
        prefer_provider=prefer_provider,
        json_schema={"name": "episode_step_outline", "schema": outline_schema},
        system_prompt=prompt_manager.render_prompt(
            PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
        ),
    )
    latest_text = (
        outline_resp.data
        if isinstance(outline_resp.data, str)
        else ("" if outline_resp.data is None else str(outline_resp.data))
    )
    reasoning = ["outline_ok"] if outline_resp.success else ["outline_failed"]
    provider_used = outline_resp.provider
    model_used = outline_resp.model
    usage = outline_resp.usage

    missing_fields: list[str] = []
    step_outlines: dict[str, Any] | None = None

    for attempt in range(3):
        parsed = (
            extract_json_block(latest_text)
            if isinstance(latest_text, str)
            else (latest_text if isinstance(latest_text, dict) else None)
        )
        if parsed:
            try:
                validated = EpisodeStepOutlineModel.model_validate(parsed)
                outlines = _normalize_outline_episodes(validated.model_dump())
                filtered = [
                    ep
                    for ep in outlines.get("episodes", [])
                    if _outline_episode_usable(ep, production_mode=production_mode)
                ]
                if len(filtered) >= episode_count:
                    outlines["episodes"] = filtered[:episode_count]
                    step_outlines = outlines
                    reasoning.append(
                        "outline_validated"
                        if attempt == 0
                        else f"outline_repaired_{attempt}"
                    )
                    break
                reasoning.append("outline_too_short")
            except Exception as exc:  # pragma: no cover - schema guard
                missing_fields = _extract_missing_fields(exc)
                reasoning.append(
                    "outline_schema_invalid"
                    if attempt == 0
                    else f"outline_schema_invalid_{attempt}"
                )
        else:
            reasoning.append(
                "outline_parse_failed"
                if attempt == 0
                else f"outline_parse_failed_{attempt}"
            )

        if attempt >= 2:
            break

        repair_prompt = prompt_manager.render_prompt(
            PromptTemplate.EPISODE_STEP_OUTLINE_REPAIR.value,
            {
                "schema": outline_schema,
                "original_prompt": outline_prompt,
                "original_output": latest_text,
                "missing_fields": missing_fields,
                "episode_count": episode_count,
            },
        )
        repair_resp = await ai_manager.generate_text(
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
            repair_resp.data
            if isinstance(repair_resp.data, str)
            else ("" if repair_resp.data is None else str(repair_resp.data))
        )
        provider_used = repair_resp.provider or provider_used
        model_used = repair_resp.model or model_used
        usage = repair_resp.usage or usage
        reasoning.append(f"outline_repair_attempt_{attempt + 1}")

    if not step_outlines:
        return OutlineGenerationResult(
            step_outlines=None,
            raw_text=latest_text,
            prompt=outline_prompt,
            provider=provider_used,
            model=model_used,
            usage=usage,
            reasoning=reasoning,
            error="outline_invalid",
        )

    return OutlineGenerationResult(
        step_outlines=step_outlines,
        raw_text=latest_text,
        prompt=outline_prompt,
        provider=provider_used,
        model=model_used,
        usage=usage,
        reasoning=reasoning,
    )


def _outline_episode_usable(episode: dict[str, Any], *, production_mode: bool) -> bool:
    if not (episode.get("logline") or "").strip():
        return False
    if not production_mode:
        return True
    beats = episode.get("beats")
    contract = episode.get("structured_episode_contract")
    return bool(beats) and isinstance(contract, dict) and bool(contract)
