import pytest
from app.api.v1 import ai_providers
from fastapi import HTTPException


class _StubResponse:
    def __init__(self, *, success: bool, error: str = "boom"):
        self.success = success
        self.error = error
        self.data = {}
        self.provider = "stub"
        self.model = "stub-model"
        self.usage = None
        self.metadata = None


class _StubAIManager:
    async def generate_text(self, **_kwargs):
        return _StubResponse(success=False)

    async def generate_image(self, **_kwargs):
        return _StubResponse(success=False)

    async def generate_video(self, **_kwargs):
        return _StubResponse(success=False)

    async def text_to_speech(self, **_kwargs):
        return _StubResponse(success=False)


class _StubAIService:
    def __init__(self):
        self.ai_manager = _StubAIManager()


@pytest.mark.asyncio
async def test_generate_video_propagates_validation_http_exception():
    with pytest.raises(HTTPException) as excinfo:
        await ai_providers.generate_video(
            ai_providers.VideoGenerationRequest(prompt=None, image_url=None),
            current_user=object(),
        )

    assert excinfo.value.status_code == 400


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("endpoint", "payload"),
    [
        (ai_providers.generate_text, ai_providers.TextGenerationRequest(prompt="hi")),
        (
            ai_providers.generate_image,
            ai_providers.ImageGenerationRequest(prompt="cat"),
        ),
        (ai_providers.generate_speech, ai_providers.SpeechGenerationRequest(text="hi")),
        (ai_providers.generate_video, ai_providers.VideoGenerationRequest(prompt="hi")),
    ],
    ids=["text", "image", "speech", "video"],
)
async def test_generate_routes_propagate_provider_http_exception(
    monkeypatch, endpoint, payload
):
    monkeypatch.setattr(ai_providers, "ai_service", _StubAIService())

    with pytest.raises(HTTPException) as excinfo:
        await endpoint(payload, current_user=object())

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "boom"
