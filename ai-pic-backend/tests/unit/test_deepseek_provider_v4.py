from __future__ import annotations

import json

import pytest
from app.services.providers.base import AIModelType, ProviderConfig
from app.services.providers.deepseek_models import (
    DEEPSEEK_BASE_URL,
    DEEPSEEK_DEFAULT_MODEL,
    DEEPSEEK_LEGACY_CHAT_MODEL,
    DEEPSEEK_V4_FLASH_MODEL,
    DEEPSEEK_V4_PRO_MODEL,
    get_static_models,
)
from app.services.providers.deepseek_provider import DeepSeekProvider
from app.services.providers.deepseek_request import build_chat_request
from app.services.providers.deepseek_text import generate_text


class _Response:
    def __init__(self, payload: dict):
        self._payload = payload
        self.content = json.dumps(payload).encode("utf-8")

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class _Client:
    def __init__(self):
        self.posts: list[dict] = []

    async def post(self, _url: str, *, json: dict):
        self.posts.append(json)
        return _Response(
            {
                "choices": [
                    {
                        "message": {
                            "content": "ok",
                            "reasoning_content": "thoughts",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 2},
            }
        )


def test_static_models_include_deepseek_v4_and_legacy_aliases():
    models = {model.model_id: model for model in get_static_models()}

    assert DEEPSEEK_V4_FLASH_MODEL in models
    assert DEEPSEEK_V4_PRO_MODEL in models
    assert models[DEEPSEEK_V4_PRO_MODEL].max_tokens == 1_000_000
    assert "thinking" in models[DEEPSEEK_V4_FLASH_MODEL].capabilities
    assert models[DEEPSEEK_LEGACY_CHAT_MODEL].metadata["deprecated"] is True
    assert (
        models[DEEPSEEK_LEGACY_CHAT_MODEL].metadata["routes_to"]
        == DEEPSEEK_V4_FLASH_MODEL
    )


def test_build_chat_request_normalizes_v4_alias_and_skips_sampling_in_thinking():
    model, payload, stream = build_chat_request(
        prompt="hi",
        model="deepseek-v4",
        max_tokens=None,
        temperature=0.7,
        top_p=0.95,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        system_prompt=None,
        extra_kwargs={},
    )

    assert model == DEEPSEEK_V4_PRO_MODEL
    assert stream is True
    assert payload["model"] == DEEPSEEK_V4_PRO_MODEL
    assert "temperature" not in payload
    assert "top_p" not in payload


def test_build_chat_request_defaults_v4_flash_to_non_thinking():
    model, payload, stream = build_chat_request(
        prompt="hi",
        model=DEEPSEEK_V4_FLASH_MODEL,
        max_tokens=32,
        temperature=0.3,
        top_p=0.5,
        frequency_penalty=0.1,
        presence_penalty=0.2,
        system_prompt=None,
        extra_kwargs={},
    )

    assert model == DEEPSEEK_V4_FLASH_MODEL
    assert stream is True
    assert payload["thinking"] == {"type": "disabled"}
    assert payload["temperature"] == 0.3
    assert payload["top_p"] == 0.5
    assert payload["max_tokens"] == 32


def test_build_chat_request_allows_sampling_when_v4_thinking_disabled():
    _model, payload, _stream = build_chat_request(
        prompt="hi",
        model=DEEPSEEK_V4_FLASH_MODEL,
        max_tokens=32,
        temperature=0.3,
        top_p=0.5,
        frequency_penalty=0.1,
        presence_penalty=0.2,
        system_prompt="system",
        extra_kwargs={"thinking": False, "stream": False},
    )

    assert payload["thinking"] == {"type": "disabled"}
    assert payload["temperature"] == 0.3
    assert payload["top_p"] == 0.5
    assert payload["max_tokens"] == 32
    assert payload["messages"][0]["role"] == "system"


@pytest.mark.asyncio
async def test_generate_text_defaults_to_v4_flash_non_stream():
    client = _Client()

    response = await generate_text(
        client=client,
        base_url=DEEPSEEK_BASE_URL,
        provider_name="deepseek",
        prompt="hi",
        stream=False,
    )

    assert response.success is True
    assert response.model == DEEPSEEK_DEFAULT_MODEL
    assert response.data == "ok"
    assert response.metadata["has_reasoning_content"] is True
    assert client.posts[-1]["model"] == DEEPSEEK_V4_FLASH_MODEL
    assert client.posts[-1]["thinking"] == {"type": "disabled"}


@pytest.mark.asyncio
async def test_provider_uses_official_base_url_and_remote_v4_metadata(monkeypatch):
    provider = DeepSeekProvider(
        ProviderConfig(name="deepseek", api_key="test", base_url=None)
    )
    assert provider.base_url == DEEPSEEK_BASE_URL
    legacy_url_provider = DeepSeekProvider(
        ProviderConfig(
            name="deepseek",
            api_key="test",
            base_url=f"{DEEPSEEK_BASE_URL}/v1",
        )
    )
    assert legacy_url_provider.base_url == DEEPSEEK_BASE_URL

    class _ModelsClient:
        async def get(self, _url: str):
            return _Response({"data": [{"id": DEEPSEEK_V4_PRO_MODEL}]})

    async def _client():
        return _ModelsClient()

    monkeypatch.setattr(provider, "get_client", _client)
    models = await provider.fetch_remote_models(AIModelType.TEXT_GENERATION)

    assert models[0].model_id == DEEPSEEK_V4_PRO_MODEL
    assert "long_context" in models[0].capabilities
