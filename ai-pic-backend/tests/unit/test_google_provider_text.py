from __future__ import annotations

import httpx
import pytest
from app.services.providers.google_provider.text import (
    generate_text,
    stream_generate_content,
)


class _DummyStreamResponse:
    def __init__(
        self, *, status_code: int, lines: list[str], body: bytes = b""
    ) -> None:
        self.status_code = status_code
        self._lines = lines
        self._body = body
        self.request = httpx.Request("POST", "http://example.test")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):  # noqa: ANN001
        return False

    async def aread(self) -> bytes:
        return self._body

    async def aiter_lines(self):
        for line in self._lines:
            yield line


class _DummyPostResponse:
    def __init__(self, json_data):
        self._json_data = json_data

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._json_data


class _DummyClient:
    def __init__(
        self,
        *,
        stream_response: _DummyStreamResponse,
        post_response: _DummyPostResponse,
    ):
        self._stream_response = stream_response
        self._post_response = post_response
        self.stream_calls: list[str] = []
        self.post_calls: list[str] = []
        self.last_stream_json = None
        self.last_post_json = None

    def stream(self, method: str, endpoint: str, json):  # noqa: ANN001
        self.stream_calls.append(endpoint)
        self.last_stream_json = json
        self._stream_response.request = httpx.Request(method, endpoint)
        return self._stream_response

    async def post(self, endpoint: str, json):  # noqa: ANN001
        self.post_calls.append(endpoint)
        self.last_post_json = json
        return self._post_response


@pytest.mark.asyncio
async def test_stream_generate_content_accepts_list_events():
    client = _DummyClient(
        stream_response=_DummyStreamResponse(
            status_code=200,
            lines=[
                'data: [{"candidates":[{"content":{"parts":[{"text":"Hello"}]}}],"usageMetadata":{"promptTokenCount":1}}]',
                "data: [DONE]",
            ],
        ),
        post_response=_DummyPostResponse({"candidates": []}),
    )

    text, usage = await stream_generate_content(client, "http://example.test", body={})

    assert text == "Hello"
    assert usage.get("promptTokenCount") == 1


@pytest.mark.asyncio
async def test_generate_text_falls_back_to_generate_content_endpoint_after_stream_failure():
    client = _DummyClient(
        stream_response=_DummyStreamResponse(
            status_code=504,
            lines=[],
            body=b"<html>504</html>",
        ),
        post_response=_DummyPostResponse(
            {
                "candidates": [{"content": {"parts": [{"text": "ok"}]}}],
                "usageMetadata": {"promptTokenCount": 2},
            }
        ),
    )

    resp = await generate_text(
        client=client,
        base_url="https://generativelanguage.googleapis.com",
        provider_name="google",
        api_key="fake",
        default_model="gemini-3-pro-preview",
        prompt="hi",
    )

    assert resp.success is True
    assert resp.data == "ok"
    assert client.stream_calls and client.stream_calls[0].endswith(
        ":streamGenerateContent?alt=sse"
    )
    assert client.post_calls and client.post_calls[0].endswith(":generateContent")


@pytest.mark.asyncio
async def test_generate_text_parses_list_payload_from_non_stream_response():
    client = _DummyClient(
        stream_response=_DummyStreamResponse(status_code=200, lines=[]),
        post_response=_DummyPostResponse(
            [
                {"candidates": [{"content": {"parts": [{"text": "A"}]}}]},
                {"usageMetadata": {"promptTokenCount": 3, "totalTokenCount": 5}},
            ]
        ),
    )

    resp = await generate_text(
        client=client,
        base_url="https://generativelanguage.googleapis.com",
        provider_name="google",
        api_key="fake",
        default_model="gemini-3-pro-preview",
        prompt="hi",
        stream=False,
        format_error=str,
    )

    assert resp.success is True
    assert resp.data == "A"
    assert resp.usage and resp.usage.get("prompt_tokens") == 3


@pytest.mark.asyncio
async def test_generate_text_uses_system_instruction_instead_of_system_role():
    client = _DummyClient(
        stream_response=_DummyStreamResponse(
            status_code=504, lines=[], body=b"<html>504</html>"
        ),
        post_response=_DummyPostResponse(
            {
                "candidates": [{"content": {"parts": [{"text": "ok"}]}}],
                "usageMetadata": {"promptTokenCount": 1},
            }
        ),
    )

    resp = await generate_text(
        client=client,
        base_url="https://generativelanguage.googleapis.com",
        provider_name="google",
        api_key="fake",
        default_model="gemini-3-pro-preview",
        prompt="hi",
        system_prompt="SYSTEM",
    )

    assert resp.success is True
    assert client.last_post_json and client.last_post_json.get("systemInstruction") == {
        "parts": [{"text": "SYSTEM"}]
    }
    assert client.last_post_json and all(
        content.get("role") != "system"
        for content in client.last_post_json.get("contents", [])
    )
