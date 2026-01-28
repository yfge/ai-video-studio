from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar

from app.utils.json_utils import extract_json_block
from pydantic import BaseModel, ValidationError

TModel = TypeVar("TModel", bound=BaseModel)


def coerce_text(value: Any) -> str:
    """Return a stable string representation of provider outputs."""
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)
    return str(value)


def parse_json_dict(payload: Any) -> Optional[Dict[str, Any]]:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        return extract_json_block(payload)
    return None


def validate_payload(
    model: Type[TModel],
    payload: Any,
    *,
    extractor: Optional[Callable[[Any], Dict[str, Any]]] = None,
) -> Tuple[
    Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]
]:
    """
    Validate a provider output against a Pydantic model.

    Returns (normalized, validation_errors, raw_json) where:
    - normalized is the model_dump() dict when validation succeeds.
    - validation_errors is a JSON-serializable Pydantic error list when validation fails.
    - raw_json is the extracted JSON dict (before model_dump), if available.
    """
    raw_json = parse_json_dict(payload)
    if extractor is not None:
        raw_json = extractor(raw_json)

    if not isinstance(raw_json, dict) or not raw_json:
        return (
            None,
            [{"loc": [], "msg": "missing json object", "type": "value_error"}],
            raw_json,
        )

    try:
        parsed = model.model_validate(raw_json)
        return parsed.model_dump(), None, raw_json
    except ValidationError as exc:
        return None, exc.errors(), raw_json


def build_repair_prompt(
    *,
    base_prompt: str,
    schema_name: str,
    prior_output: str,
    validation_errors: Optional[List[Dict[str, Any]]],
) -> str:
    errors_text = (
        json.dumps(validation_errors, ensure_ascii=False) if validation_errors else "[]"
    )
    prior = (prior_output or "").strip()
    if len(prior) > 12000:
        prior = prior[:12000] + "\n...(truncated)..."

    return (
        base_prompt
        + "\n\n"
        + "你上一次的输出不符合 JSON Schema，请修复并重新输出。\n"
        + "要求：\n"
        + "- 只输出 JSON（不要代码块，不要解释）\n"
        + "- 严格符合 JSON Schema，字段类型必须正确\n"
        + "- 缺失字段必须补齐；不要返回 null 以逃避字段\n"
        + "- 不要添加 schema 之外的字段\n"
        + f"- schema_name: {schema_name}\n\n"
        + "上一次输出：\n"
        + prior
        + "\n\n"
        + "校验错误（Pydantic errors）：\n"
        + errors_text
    )


async def generate_with_repair(
    *,
    ai_manager: Any,
    base_prompt: str,
    model: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
    schema_name: str,
    schema: Dict[str, Any],
    system_prompt: Optional[str],
    repair_system_prompt: Optional[str] = None,
    pydantic_model: Type[TModel],
    extractor: Optional[Callable[[Any], Dict[str, Any]]] = None,
    extra_validator: Optional[
        Callable[[Dict[str, Any]], Optional[List[Dict[str, Any]]]]
    ] = None,
    max_repairs: int = 2,
) -> Dict[str, Any]:
    """
    Generate structured JSON using AI manager and repair invalid outputs.

    Returns:
    - content: last raw text
    - normalized: validated dict or None
    - validation_errors: final validation errors (when normalized is None)
    - raw_json: last extracted json dict (best-effort)
    - repair_attempts: list of attempts (excluding the initial try)
    - first_attempt: first attempt payload
    """
    response = await ai_manager.generate_text(
        prompt=base_prompt,
        temperature=temperature,
        model=model,
        prefer_provider=prefer_provider,
        json_schema={"name": schema_name, "schema": schema},
        system_prompt=system_prompt,
    )
    content_text = coerce_text(getattr(response, "data", None))
    normalized, errors, raw_json = validate_payload(
        pydantic_model, content_text, extractor=extractor
    )
    if normalized is not None and extra_validator is not None:
        extra_errors = extra_validator(normalized)
        if extra_errors:
            normalized = None
            errors = extra_errors

    first_attempt = {
        "success": bool(getattr(response, "success", False)),
        "provider_used": getattr(response, "provider", None),
        "model_used": getattr(response, "model", None),
        "usage": getattr(response, "usage", None),
        "content": content_text,
        "normalized": normalized,
        "validation_errors": errors,
    }

    repair_attempts: List[Dict[str, Any]] = []
    if normalized is not None:
        return {
            "content": content_text,
            "normalized": normalized,
            "validation_errors": None,
            "raw_json": raw_json,
            "repair_attempts": repair_attempts,
            "first_attempt": first_attempt,
        }

    for _ in range(max_repairs):
        repair_prompt = build_repair_prompt(
            base_prompt=base_prompt,
            schema_name=schema_name,
            prior_output=content_text,
            validation_errors=errors,
        )
        repair = await ai_manager.generate_text(
            prompt=repair_prompt,
            temperature=temperature,
            model=model,
            prefer_provider=prefer_provider,
            json_schema={"name": schema_name, "schema": schema},
            system_prompt=repair_system_prompt or system_prompt,
        )
        content_text = coerce_text(getattr(repair, "data", None))
        normalized, errors, raw_json = validate_payload(
            pydantic_model, content_text, extractor=extractor
        )
        if normalized is not None and extra_validator is not None:
            extra_errors = extra_validator(normalized)
            if extra_errors:
                normalized = None
                errors = extra_errors
        repair_attempts.append(
            {
                "success": bool(getattr(repair, "success", False)),
                "provider_used": getattr(repair, "provider", None),
                "model_used": getattr(repair, "model", None),
                "usage": getattr(repair, "usage", None),
                "prompt": repair_prompt,
                "content": content_text,
                "normalized": normalized,
                "validation_errors": errors,
            }
        )
        if normalized is not None:
            return {
                "content": content_text,
                "normalized": normalized,
                "validation_errors": None,
                "raw_json": raw_json,
                "repair_attempts": repair_attempts,
                "first_attempt": first_attempt,
            }

    return {
        "content": content_text,
        "normalized": None,
        "validation_errors": errors,
        "raw_json": raw_json,
        "repair_attempts": repair_attempts,
        "first_attempt": first_attempt,
    }
