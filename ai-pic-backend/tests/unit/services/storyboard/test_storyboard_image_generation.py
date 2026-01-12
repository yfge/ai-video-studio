import pytest
from app.services.storyboard.storyboard_image_generation import (
    generate_storyboard_image_urls,
)


class _DummyResponse:
    def __init__(
        self,
        *,
        success: bool,
        data: dict,
        provider: str | None = None,
        model: str | None = None,
        metadata: dict | None = None,
        error: str | None = None,
    ) -> None:
        self.success = success
        self.data = data
        self.provider = provider
        self.model = model
        self.metadata = metadata
        self.error = error


class _DummyManager:
    def __init__(self, response: _DummyResponse) -> None:
        self._response = response
        self.last_call: tuple[str, dict] | None = None

    async def generate_image(self, **kwargs):
        self.last_call = ("generate_image", kwargs)
        return self._response

    async def image_to_image(self, **kwargs):
        self.last_call = ("image_to_image", kwargs)
        return self._response


class _DummyAIService:
    def __init__(self, response: _DummyResponse) -> None:
        self.ai_manager = _DummyManager(response)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_storyboard_text_to_image_uses_provider_safe_kwargs():
    ai_service = _DummyAIService(
        _DummyResponse(
            success=True,
            data={"images": ["https://example.com/out.png"]},
            provider="volcengine",
            model="doubao-seedream-4-5-251128",
        )
    )

    result = await generate_storyboard_image_urls(
        prompt="test prompt",
        refs=[],
        model="volcengine:doubao-seedream-4-5-251128",
        count=2,
        size="2K",
        aspect_ratio="1:1",
        width=1024,
        height=1024,
        style="realistic",
        style_preset_id=None,
        style_spec=None,
        ai_service=ai_service,
        backend_base="http://backend.local",
    )

    method, kwargs = ai_service.ai_manager.last_call or ("", {})
    assert method == "generate_image"
    assert kwargs["prefer_provider"] == "volcengine"
    assert kwargs["model"] == "doubao-seedream-4-5-251128"
    assert kwargs["size"] == "2K"
    assert kwargs["n"] == 2
    assert "width" not in kwargs
    assert "height" not in kwargs
    assert result["urls"] == ["https://example.com/out.png"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_storyboard_image_to_image_preserves_extra_images_for_supported_provider():
    ai_service = _DummyAIService(
        _DummyResponse(
            success=True,
            data={"images": ["https://example.com/out-1.png"]},
            provider="keling",
            model="kling-image-v2",
            metadata={"style_spec": {"foo": "bar"}},
        )
    )

    result = await generate_storyboard_image_urls(
        prompt="variant prompt",
        refs=[
            "https://example.com/base.png",
            "https://example.com/extra.png",
        ],
        model="keling:kling-image-v2",
        count=3,
        size="1024x1024",
        aspect_ratio="1:1",
        width=1024,
        height=1024,
        style="realistic",
        style_preset_id="realistic_cinematic",
        style_spec={"foo": "bar"},
        ai_service=ai_service,
        backend_base="http://backend.local",
    )

    method, kwargs = ai_service.ai_manager.last_call or ("", {})
    assert method == "image_to_image"
    assert kwargs["prefer_provider"] == "keling"
    assert kwargs["model"] == "kling-image-v2"
    assert kwargs["count"] == 3
    assert kwargs["image_url"] == "https://example.com/base.png"
    assert kwargs["extra_images"] == ["https://example.com/extra.png"]
    assert "width" not in kwargs
    assert "height" not in kwargs
    assert result["urls"] == ["https://example.com/out-1.png"]
    assert result["image_gen"]["generation_profile"] == "balanced"
    assert result["image_gen"]["image_fidelity"] == 0.5
    assert result["image_gen"]["human_fidelity"] == 0.45
    assert result["image_gen"]["reference_images_count"] == 1
