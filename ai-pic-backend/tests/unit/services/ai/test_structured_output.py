from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest
from app.services.ai.structured_output import (
    build_repair_prompt,
    generate_with_repair,
    validate_payload,
)
from pydantic import BaseModel, Field


class _TinySchema(BaseModel):
    title: str = Field(..., min_length=1)
    count: int = Field(..., ge=1)


@pytest.mark.unit
def test_validate_payload_accepts_valid_dict() -> None:
    normalized, errors, raw = validate_payload(_TinySchema, {"title": "ok", "count": 2})
    assert errors is None
    assert raw == {"title": "ok", "count": 2}
    assert normalized == {"title": "ok", "count": 2}


@pytest.mark.unit
def test_validate_payload_parses_json_string() -> None:
    normalized, errors, raw = validate_payload(_TinySchema, '{"title":"ok","count":2}')
    assert errors is None
    assert raw == {"title": "ok", "count": 2}
    assert normalized == {"title": "ok", "count": 2}


@pytest.mark.unit
def test_validate_payload_returns_errors_for_invalid_payload() -> None:
    normalized, errors, raw = validate_payload(_TinySchema, '{"title":"ok"}')
    assert normalized is None
    assert raw == {"title": "ok"}
    assert isinstance(errors, list)
    assert any("count" in str(err.get("loc")) for err in errors or [])


@pytest.mark.unit
def test_build_repair_prompt_includes_schema_name_and_errors() -> None:
    prompt = build_repair_prompt(
        base_prompt="BASE",
        schema_name="tiny",
        prior_output='{"title":"ok"}',
        validation_errors=[
            {"loc": ["count"], "msg": "Field required", "type": "missing"}
        ],
    )
    assert "schema_name: tiny" in prompt
    assert "BASE" in prompt
    assert "Field required" in prompt


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_with_repair_repairs_invalid_output() -> None:
    calls: List[Dict[str, Any]] = []

    class _MockAIManager:
        def __init__(self) -> None:
            self._idx = 0

        async def generate_text(self, prompt: str, **_: Any) -> Any:
            calls.append({"prompt": prompt})
            self._idx += 1
            if self._idx == 1:
                return SimpleNamespace(
                    success=True,
                    data='{"title":"ok"}',
                    provider="mock",
                    model="mock-model",
                    usage={"total_tokens": 1},
                )
            return SimpleNamespace(
                success=True,
                data='{"title":"ok","count":2}',
                provider="mock",
                model="mock-model",
                usage={"total_tokens": 2},
            )

    result = await generate_with_repair(
        ai_manager=_MockAIManager(),
        base_prompt="BASE",
        model=None,
        prefer_provider=None,
        temperature=0.7,
        schema_name="tiny",
        schema=_TinySchema.model_json_schema(),
        system_prompt=None,
        pydantic_model=_TinySchema,
        extractor=None,
        max_repairs=2,
    )

    assert result["normalized"] == {"title": "ok", "count": 2}
    assert result["validation_errors"] is None
    assert isinstance(result.get("first_attempt"), dict)
    assert len(result.get("repair_attempts") or []) == 1
    assert len(calls) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_with_repair_applies_extra_validator() -> None:
    calls: List[Dict[str, Any]] = []

    class _MockAIManager:
        def __init__(self) -> None:
            self._idx = 0

        async def generate_text(self, prompt: str, **_: Any) -> Any:
            calls.append({"prompt": prompt})
            self._idx += 1
            if self._idx == 1:
                return SimpleNamespace(
                    success=True,
                    data='{"title":"ok","count":1}',
                    provider="mock",
                    model="mock-model",
                    usage={"total_tokens": 1},
                )
            return SimpleNamespace(
                success=True,
                data='{"title":"ok","count":2}',
                provider="mock",
                model="mock-model",
                usage={"total_tokens": 2},
            )

    def _extra_validator(payload: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        if payload.get("count") != 2:
            return [
                {
                    "loc": ["count"],
                    "msg": "expected count=2",
                    "type": "value_error.count_mismatch",
                }
            ]
        return None

    result = await generate_with_repair(
        ai_manager=_MockAIManager(),
        base_prompt="BASE",
        model=None,
        prefer_provider=None,
        temperature=0.7,
        schema_name="tiny",
        schema=_TinySchema.model_json_schema(),
        system_prompt=None,
        pydantic_model=_TinySchema,
        extractor=None,
        extra_validator=_extra_validator,
        max_repairs=2,
    )

    assert result["normalized"] == {"title": "ok", "count": 2}
    assert result["validation_errors"] is None
    assert len(result.get("repair_attempts") or []) == 1
    assert len(calls) == 2
