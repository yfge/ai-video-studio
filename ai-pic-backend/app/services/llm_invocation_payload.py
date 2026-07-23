from __future__ import annotations

import json
from typing import Any


def normalize_token_usage(
    usage: Any, metadata: Any = None
) -> tuple[int | None, int | None, int | None]:
    usage_dict = usage if isinstance(usage, dict) else {}
    metadata_dict = metadata if isinstance(metadata, dict) else {}
    raw = metadata_dict.get("raw")
    raw_dict = raw if isinstance(raw, dict) else {}
    raw_usage = raw_dict.get("usageMetadata")
    raw_usage_dict = raw_usage if isinstance(raw_usage, dict) else raw_dict

    input_tokens = _first_int(
        usage_dict,
        "input_tokens",
        "prompt_tokens",
        "promptTokenCount",
    )
    if input_tokens is None:
        input_tokens = _first_int(raw_usage_dict, "input_tokens", "promptTokenCount")
    output_tokens = _first_int(
        usage_dict,
        "output_tokens",
        "completion_tokens",
        "candidatesTokenCount",
    )
    if output_tokens is None:
        output_tokens = _first_int(
            raw_usage_dict, "output_tokens", "candidatesTokenCount"
        )
    cache_tokens = _first_int(
        usage_dict,
        "cache_tokens",
        "cached_tokens",
        "prompt_cache_hit_tokens",
        "cache_read_input_tokens",
        "cachedContentTokenCount",
    )
    if cache_tokens is None:
        for details_key in ("input_tokens_details", "prompt_tokens_details"):
            details = usage_dict.get(details_key)
            if isinstance(details, dict):
                cache_tokens = _first_int(details, "cached_tokens")
                if cache_tokens is not None:
                    break
    if cache_tokens is None:
        cache_tokens = _first_int(
            raw_usage_dict, "cachedContentTokenCount", "cached_tokens"
        )
    return input_tokens, cache_tokens, output_tokens


def serialize_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


def json_safe(value: Any) -> Any:
    if value is None:
        return None
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def _first_int(values: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = values.get(key)
        if value is not None and not isinstance(value, bool):
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
    return None
