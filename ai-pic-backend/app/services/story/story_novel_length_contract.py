"""Preset resolution and bounded model-capacity checks for novel lengths."""

import hashlib
import json
import math
import re

from app.schemas.story_novel_export import NovelLengthRange
from fastapi import HTTPException

_PRESETS = (
    ("commercial_serial", "商业网文短章", 2000, 2500, 3000),
    ("short_serial", "短章连载", 1500, 2200, 3000),
    ("standard_serial", "标准网文", 3000, 4000, 5000),
    ("long_chapter", "长章模式", 4500, 6000, 8000),
)
_KNOWN_OUTPUT_LIMITS = {
    "doubao-lite-4k": 4096,
    "doubao-pro-4k": 4096,
    "abab6.5s-chat": 8192,
}
_MIN_NOVEL_OUTPUT_TOKENS = 16000
_MODEL_OUTPUT_FLOORS = {"deepseek-v4-pro": 48000}


def non_whitespace_chars(value: str) -> int:
    return len(re.sub(r"\s+", "", value or ""))


def chapter_length_range(chapter_plan: dict) -> tuple[int, int, int]:
    return (
        int(chapter_plan.get("min_chars") or 3000),
        int(chapter_plan["target_chars"]),
        int(chapter_plan.get("max_chars") or 5000),
    )


def chapter_output_tokens(chapter_plan: dict, model: str | None = None) -> int:
    return max(
        _model_output_floor(model),
        dynamic_output_tokens(chapter_length_range(chapter_plan)[2]),
    )


def list_length_profiles() -> list[dict]:
    return [
        {
            "profile_id": profile_id,
            "name": name,
            "count_mode": "non_whitespace_chars",
            "min_chars": minimum,
            "target_chars": target,
            "max_chars": maximum,
        }
        for profile_id, name, minimum, target, maximum in _PRESETS
    ]


def dynamic_output_tokens(max_chars: int) -> int:
    return max(2048, math.ceil(max_chars * 1.6) + 1500)


def _model_output_floor(model: str | None) -> int:
    model_id = (model or "").split(":", 1)[-1]
    return _MODEL_OUTPUT_FLOORS.get(model_id, _MIN_NOVEL_OUTPUT_TOKENS)


def validate_model_capacity(model: str | None, max_chars: int) -> None:
    model_id = (model or "").split(":", 1)[-1]
    limit = _KNOWN_OUTPUT_LIMITS.get(model_id)
    required = max(_MIN_NOVEL_OUTPUT_TOKENS, dynamic_output_tokens(max_chars))
    if limit is not None and limit < required:
        raise HTTPException(
            status_code=422,
            detail=(
                f"模型 {model_id} 的已知输出能力 {limit} tokens "
                f"不足以覆盖章节上限 {max_chars} 字（预计需要 {required} tokens）"
            ),
        )


def resolve_profile(profile_id: str, custom: NovelLengthRange | None) -> dict:
    if profile_id == "custom":
        if custom is None:
            raise HTTPException(
                status_code=422, detail="custom 规格必须提供 custom_length_profile"
            )
        minimum, target, maximum = (
            custom.min_chars,
            custom.target_chars,
            custom.max_chars,
        )
        name = "自定义"
    else:
        row = next((item for item in _PRESETS if item[0] == profile_id), None)
        if not row:
            raise HTTPException(status_code=422, detail="未知长度规格")
        _, name, minimum, target, maximum = row
    return {
        "profile_id": profile_id,
        "profile_name": name,
        "count_mode": "non_whitespace_chars",
        "default_min_chars": minimum,
        "default_target_chars": target,
        "default_max_chars": maximum,
    }


def normalize_overrides(
    raw: dict[str, NovelLengthRange], positions: list[int]
) -> dict[int, NovelLengthRange]:
    normalized = {}
    for key, value in raw.items():
        if not str(key).isdigit() or int(key) < 1:
            raise HTTPException(status_code=422, detail=f"无效章节覆盖位置: {key}")
        normalized[int(key)] = value
    unknown = sorted(set(normalized).difference(positions))
    if unknown:
        raise HTTPException(status_code=422, detail=f"章节覆盖不存在: {unknown}")
    return normalized


def content_hash(value: dict) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()
