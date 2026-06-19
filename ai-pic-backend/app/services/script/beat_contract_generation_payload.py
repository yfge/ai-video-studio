from __future__ import annotations

from typing import Any

from app.services.script.beat_contract_normalizer import (
    flatten_contract_to_script_payload,
    normalize_script_beat_contract,
)


def normalize_and_flatten_payload(
    parsed: dict[str, Any],
    *,
    episode: dict[str, Any],
    format_type: str,
    language: str,
    template_style: str,
    target_chars_per_episode: int,
) -> tuple[Any, dict[str, Any]]:
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
    return contract, flattened


def response_diagnostics(response: Any, *, max_tokens: int) -> str:
    metadata = getattr(response, "metadata", None)
    if not isinstance(metadata, dict):
        metadata = {}
    usage = getattr(response, "usage", None)
    if not isinstance(usage, dict):
        usage = {}
    completion_details = usage.get("completion_tokens_details")
    if not isinstance(completion_details, dict):
        completion_details = {}

    fields = {
        "provider": getattr(response, "provider", None),
        "model": getattr(response, "model", None),
        "finish_reason": metadata.get("finish_reason"),
        "max_tokens": max_tokens,
        "completion_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": completion_details.get("reasoning_tokens"),
    }
    return ", ".join(
        f"{key}={value}" for key, value in fields.items() if value is not None
    )
