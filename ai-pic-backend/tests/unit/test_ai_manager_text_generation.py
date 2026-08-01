from __future__ import annotations

import asyncio
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
    started: list[dict[str, Any]] = []
    finished: list[tuple[dict[str, Any], dict[str, Any]]] = []

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
                usage={
                    "prompt_tokens": 10,
                    "completion_tokens": 4,
                    "prompt_tokens_details": {"cached_tokens": 3},
                },
            )

    providers = {
        "deepseek": _Provider("deepseek", "deepseek-v4-flash", succeeds=False),
        "openai": _Provider("openai", "gpt-4o", succeeds=True),
    }
    references = [{"type": "prompt_template", "value": {"template": "novel"}}]
    provider_kwargs = {"invocation_input_references": references}

    async def _get_models(provider: Any, _model_type: Any) -> list[ModelInfo]:
        return provider.available_models

    def _begin(**payload: Any) -> dict[str, Any]:
        payload["row_id"] = len(started) + 1
        started.append(payload)
        return payload

    def _finish(handle: dict[str, Any], **payload: Any) -> None:
        finished.append((handle, payload))

    result = await generate_text_with_fallback(
        prompt="Return JSON",
        model="deepseek-v4-flash",
        prefer_provider=None,
        system_prompt=None,
        max_tokens=100,
        temperature=0.2,
        json_schema={"type": "object"},
        stream=False,
        call_scene="tests.story_generation",
        provider_kwargs=provider_kwargs,
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
        begin_invocation=_begin,
        finish_invocation=_finish,
    )

    assert result.success is True
    assert result.provider == "openai"
    assert result.model == "gpt-4o"
    assert calls == [
        ("deepseek", "deepseek-v4-flash"),
        ("openai", "gpt-4o"),
    ]
    assert [item["attempt_index"] for item in started] == [1, 2]
    assert [item["provider"] for item in started] == ["deepseek", "openai"]
    assert all(item["prompt"] == "Return JSON" for item in started)
    assert all(item["call_scene"] == "tests.story_generation" for item in started)
    assert all(item["input_references"] == references for item in started)
    assert "invocation_input_references" not in provider_kwargs
    assert [payload["response"].success for _, payload in finished] == [False, True]
    assert result.metadata["llm_invocation_id"] == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_text_cancellation_closes_processing_invocation() -> None:
    started = asyncio.Event()
    finished = []

    class _Provider:
        name = "deepseek"
        available_models = [_model("deepseek-v4-pro")]
        default_model = "deepseek-v4-pro"

        async def generate_text(self, **_kwargs: Any) -> AIResponse:
            started.set()
            await asyncio.sleep(10)
            raise AssertionError("cancelled provider returned")

    async def get_models(provider: Any, _model_type: Any) -> list[ModelInfo]:
        return provider.available_models

    task = asyncio.create_task(
        generate_text_with_fallback(
            prompt="brief",
            model="deepseek-v4-pro",
            prefer_provider="deepseek",
            system_prompt=None,
            max_tokens=100,
            temperature=0.0,
            json_schema=None,
            stream=False,
            call_scene="tests.chapter_planning.2",
            provider_kwargs={},
            providers={"deepseek": _Provider()},
            max_retries=1,
            enable_fallback=False,
            resolve_prefer_provider_and_model=lambda model, provider: (
                provider,
                model,
            ),
            get_available_providers=lambda **_: ["deepseek"],
            select_provider=lambda available, _prefer: available[0],
            update_request_count=lambda _provider: None,
            get_models_for_type=get_models,
            log_request=lambda **_: None,
            log_prompt=lambda _prompt: None,
            log_response=lambda **_: None,
            begin_invocation=lambda **payload: payload,
            finish_invocation=lambda handle, **payload: finished.append(
                (handle, payload)
            ),
        )
    )
    await started.wait()
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert finished[0][1]["error"] == "provider call cancelled"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_required_audit_start_failure_stops_before_provider() -> None:
    calls = []

    class _Provider:
        name = "deepseek"
        available_models = [_model("deepseek-v4-pro")]
        default_model = "deepseek-v4-pro"

        async def generate_text(self, **_kwargs: Any) -> AIResponse:
            calls.append("provider")
            raise AssertionError("provider must not be called")

    async def get_models(provider: Any, _model_type: Any) -> list[ModelInfo]:
        return provider.available_models

    with pytest.raises(RuntimeError, match="audit could not be persisted"):
        await generate_text_with_fallback(
            prompt="brief",
            model="deepseek-v4-pro",
            prefer_provider="deepseek",
            system_prompt=None,
            max_tokens=100,
            temperature=0.0,
            json_schema=None,
            stream=False,
            call_scene="tests.chapter_planning.2",
            provider_kwargs={
                "invocation_input_references": [
                    {"type": "prompt_template", "value": {"template": "novel"}}
                ]
            },
            providers={"deepseek": _Provider()},
            max_retries=1,
            enable_fallback=False,
            resolve_prefer_provider_and_model=lambda model, provider: (
                provider,
                model,
            ),
            get_available_providers=lambda **_: ["deepseek"],
            select_provider=lambda available, _prefer: available[0],
            update_request_count=lambda _provider: None,
            get_models_for_type=get_models,
            log_request=lambda **_: None,
            log_prompt=lambda _prompt: None,
            log_response=lambda **_: None,
            begin_invocation=lambda **_payload: None,
            finish_invocation=lambda *_args, **_payload: None,
        )

    assert calls == []
