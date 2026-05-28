import pytest
from app.api.v1 import ai_text_generation
from app.api.v1.api import api_router


class _StubResponse:
    success = True
    data = "ok"
    provider = "stub"
    model = "stub-model"
    usage = {"total_tokens": 1}
    metadata = {"trace": "unit"}


class _StubAIManager:
    def __init__(self) -> None:
        self.kwargs = None

    async def generate_text(self, **kwargs):
        self.kwargs = kwargs
        return _StubResponse()


class _StubAIService:
    def __init__(self) -> None:
        self.ai_manager = _StubAIManager()


def test_text_generation_route_accepts_stream_and_thinking_options() -> None:
    route = next(
        route
        for route in api_router.routes
        if getattr(route, "path", None) == "/ai/generate/text"
        and "POST" in getattr(route, "methods", set())
    )

    request_model = route.body_field.type_
    fields = getattr(request_model, "model_fields", {})

    assert route.endpoint is ai_text_generation.generate_text
    assert "stream" in fields
    assert "thinking" in fields


@pytest.mark.asyncio
async def test_generate_text_forwards_stream_and_thinking(monkeypatch) -> None:
    stub_service = _StubAIService()
    monkeypatch.setattr(ai_text_generation, "ai_service", stub_service)

    response = await ai_text_generation.generate_text(
        ai_text_generation.TextGenerationRequest(
            prompt="write a short scene",
            model="deepseek-v4-flash",
            stream=False,
            thinking=False,
            max_tokens=80,
        ),
        current_user=object(),
    )

    assert response["success"] is True
    assert response["data"]["content"] == "ok"
    assert stub_service.ai_manager.kwargs == {
        "prompt": "write a short scene",
        "model": "deepseek-v4-flash",
        "prefer_provider": None,
        "system_prompt": None,
        "temperature": 0.7,
        "stream": False,
        "thinking": False,
        "max_tokens": 80,
    }
