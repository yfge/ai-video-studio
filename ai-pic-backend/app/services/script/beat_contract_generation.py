from __future__ import annotations

from typing import Any

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.services.ai.scripts_ai_manager_payloads import (
    _BEAT_CONTRACT_MAX_TOKENS,
    _BEAT_CONTRACT_REPAIR_HINT,
    _BEAT_CONTRACT_SCHEMA_PAYLOAD,
    _REPAIR_MAX_TOKENS,
)
from app.services.script.beat_contract_normalizer import (
    flatten_contract_to_script_payload,
    normalize_script_beat_contract,
)
from app.utils.json_utils import extract_json_block


class BeatContractGenerationError(Exception):
    def __init__(
        self, code: str, *, raw: Any = None, detail: str | None = None
    ) -> None:
        super().__init__(code)
        self.code = code
        self.raw = raw
        self.detail = detail


def story_with_default_script_format(
    story: dict[str, Any],
    episode: dict[str, Any],
) -> dict[str, Any]:
    prompt_story = dict(story)
    story_format = (
        prompt_story.get("story_format") or episode.get("story_format") or "short_drama"
    )
    prompt_story["story_format"] = story_format
    return prompt_story


async def generate_beat_contract_payload(
    ai_manager: Any,
    *,
    episode: dict[str, Any],
    story: dict[str, Any],
    scenes: list[Any],
    format_type: str,
    language: str,
    dialogue_style: str,
    template_style: str,
    target_chars_per_episode: int,
    quality_threshold: float,
    additional_requirements: str | None,
    temperature: float,
    model: str | None,
    prefer_provider: str | None,
) -> dict[str, Any]:
    prompt = prompt_manager.render_prompt(
        PromptTemplate.SCRIPT_BEATS.value,
        {
            "episode": episode,
            "story": story_with_default_script_format(story, episode),
            "scenes": scenes,
            "dialogue_style": dialogue_style,
            "language": language,
            "format_type": format_type,
            "template_style": template_style,
            "target_chars_per_episode": target_chars_per_episode,
            "quality_threshold": quality_threshold,
            "additional_requirements": additional_requirements or "",
        },
    )
    response = await ai_manager.generate_text(
        prompt=prompt,
        temperature=temperature,
        model=model,
        prefer_provider=prefer_provider,
        max_tokens=_BEAT_CONTRACT_MAX_TOKENS,
        json_schema=_BEAT_CONTRACT_SCHEMA_PAYLOAD,
        system_prompt="你是专业短剧结构编剧，请严格按 JSON 返回。",
        stream=False,
    )
    if not response.success:
        raise BeatContractGenerationError("beat_contract_failed", raw=response.data)

    parsed = _parse_payload(response.data)
    if not parsed:
        parsed, response = await _repair_payload(
            ai_manager,
            raw_output=response.data,
            temperature=temperature,
            model=model,
            prefer_provider=prefer_provider,
        )
    if not parsed or not isinstance(parsed, dict):
        raise BeatContractGenerationError(
            "beat_contract_invalid_json", raw=response.data
        )

    try:
        contract = normalize_script_beat_contract(parsed)
        flattened = flatten_contract_to_script_payload(
            contract,
            format_type=format_type,
            language=language,
            episode_number=episode.get("episode_number"),
            template_style=template_style,
            target_chars_per_episode=target_chars_per_episode,
            title=episode.get("title"),
        )
    except Exception as exc:
        raise BeatContractGenerationError(
            "beat_contract_invalid", raw=parsed, detail=str(exc)
        ) from exc

    return {
        "payload": {
            **flattened,
            "structured_script_contract": contract.model_dump(mode="json"),
        },
        "prompt": prompt,
        "response": response,
    }


async def _repair_payload(
    ai_manager: Any,
    *,
    raw_output: Any,
    temperature: float,
    model: str | None,
    prefer_provider: str | None,
) -> tuple[dict[str, Any] | None, Any]:
    repair_prompt = (
        "上一次输出无法解析为 JSON 或不符合要求，请修复。\n"
        "要求：只返回严格 JSON（不要代码块/不要解释/不要额外文本）。\n"
        f"输出结构示例（字段必须齐全）：\n{_BEAT_CONTRACT_REPAIR_HINT}\n\n"
        f"raw_output:\n{raw_output}"
    )
    repair_resp = await ai_manager.generate_text(
        prompt=repair_prompt,
        temperature=min(0.3, temperature),
        model=model,
        prefer_provider=prefer_provider,
        max_tokens=_REPAIR_MAX_TOKENS,
        json_schema=_BEAT_CONTRACT_SCHEMA_PAYLOAD,
        system_prompt=prompt_manager.render_prompt(
            PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
        ),
        stream=False,
    )
    return _parse_payload(repair_resp.data), repair_resp


def _parse_payload(raw: Any) -> dict[str, Any] | None:
    if isinstance(raw, dict):
        return raw
    if raw is None:
        return None
    if isinstance(raw, str):
        return extract_json_block(raw)
    return extract_json_block(str(raw))
