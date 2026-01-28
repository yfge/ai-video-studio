from __future__ import annotations

from typing import Any, Dict

from app.schemas.generation import StoryOutlineModel
from app.utils.json_utils import extract_json_block
from app.utils.story_parser import extract_story_outline_payload
from fastapi import HTTPException
from pydantic import ValidationError


def normalize_story_outline_strict(result: Any) -> Dict[str, Any]:
    """Strictly validate AI output; do not persist heuristic text fallbacks."""
    if not isinstance(result, dict):
        raise HTTPException(status_code=500, detail="AI故事生成失败：返回格式错误")

    normalized = result.get("normalized")
    if isinstance(normalized, dict) and normalized:
        try:
            return StoryOutlineModel.model_validate(normalized).model_dump()
        except ValidationError:
            # Fall through to best-effort JSON extraction/normalization.
            pass

    content = result.get("content")
    raw = extract_json_block(content) if isinstance(content, str) else None
    extracted = extract_story_outline_payload(raw) if raw else {}
    if extracted:
        try:
            return StoryOutlineModel.model_validate(extracted).model_dump()
        except ValidationError as exc:
            errors = exc.errors()
            raise HTTPException(
                status_code=500,
                detail=f"AI故事生成失败：输出不符合 schema（{len(errors)} errors）",
            ) from exc

    errors = result.get("validation_errors")
    if errors:
        raise HTTPException(
            status_code=500,
            detail=f"AI故事生成失败：输出不符合 schema（validation_errors={errors}）",
        )

    raise HTTPException(status_code=500, detail="AI故事生成失败：未返回可解析的 JSON")
