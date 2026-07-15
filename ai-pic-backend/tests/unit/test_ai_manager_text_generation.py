from __future__ import annotations

from typing import Any

import pytest
from app.services.ai_manager_text_generation import generate_text_with_fallback
from app.services.providers.base import AIModelType, AIResponse, AITaskType, ModelInfo


def _model(model_id: str) -> ModelInfo:
    return ModelInfo(
        model_id=model_id,
        name=model_id,
        description=model_id,
        model_type=AIModelType.TEXT_GENERATION,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_text_fallback_uses_fallback_provider_model() -> None:
    calls: list[tuple[str, str | None]] = []

    class _Provider:
        def __init__(self, name: str, model_id: str, *, succeeds: bool) -> None:
            self.name = name
            self.available_models = [_model(model_id)]
            self.default_model = model_id
            self.succeeds = succeeds

        async def generate_text(self, **kwargs: Any) -> AIResponse:
            model = kwargs.get("model")
            calls.append((self.name, model))
            if model != self.default_model:
                raise ValueError(f"unsupported model: {model}")
            return AIResponse(
                success=self.succeeds,
                data='{"title":"ok"}' if self.succeeds else None,
                error=None if self.succeeds else "402 Insufficient Balance",
                provider=self.name,
                model=model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
            )

    providers = {
        "deepseek": _Provider("deepseek", "deepseek-v4-flash", succeeds=False),
        "openai": _Provider("openai", "gpt-4o", succeeds=True),
    }

    async def _get_models(provider: Any, _model_type: Any) -> list[ModelInfo]:
        return provider.available_models

    result = await generate_text_with_fallback(
        prompt="Return JSON",
        model="deepseek-v4-flash",
        prefer_provider=None,
        system_prompt=None,
        max_tokens=100,
        temperature=0.2,
        json_schema={"type": "object"},
        stream=False,
        provider_kwargs={},
        providers=providers,
        max_retries=2,
        enable_fallback=True,
        resolve_prefer_provider_and_model=lambda model, provider: (provider, model),
        get_available_providers=lambda **_: ["deepseek", "openai"],
        select_provider=lambda available, _prefer: available[0],
        update_request_count=lambda _provider: None,
        get_models_for_type=_get_models,
        log_request=lambda **_: None,
        log_prompt=lambda _prompt: None,
        log_response=lambda **_: None,
    )

    assert result.success is True
    assert result.provider == "openai"
    assert result.model == "gpt-4o"
    assert calls == [
        ("deepseek", "deepseek-v4-flash"),
        ("openai", "gpt-4o"),
    ]
