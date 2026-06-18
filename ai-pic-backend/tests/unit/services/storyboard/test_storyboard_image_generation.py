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
    def __init__(self, response: _DummyResponse | list[_DummyResponse]) -> None:
        self._responses = list(response) if isinstance(response, list) else [response]
        self.last_call: tuple[str, dict] | None = None
        self.calls: list[tuple[str, dict]] = []

    async def generate_image(self, **kwargs):
        self.last_call = ("generate_image", kwargs)
        self.calls.append(self.last_call)
        return self._responses.pop(0)

    async def image_to_image(self, **kwargs):
        self.last_call = ("image_to_image", kwargs)
        self.calls.append(self.last_call)
        return self._responses.pop(0)


class _DummyAIService:
    def __init__(self, response: _DummyResponse | list[_DummyResponse]) -> None:
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
async def test_storyboard_image_to_image_omits_extra_images_for_keling():
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
    assert "extra_images" not in kwargs
    assert "width" not in kwargs
    assert "height" not in kwargs
    assert result["urls"] == ["https://example.com/out-1.png"]
    assert result["image_gen"]["generation_profile"] == "balanced"
    assert result["image_gen"]["image_fidelity"] == 0.5
    assert result["image_gen"]["human_fidelity"] == 0.45
    assert result["image_gen"]["reference_images_count"] == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_storyboard_refs_use_text_to_image_when_provider_supports_reference_images():
    ai_service = _DummyAIService(
        _DummyResponse(
            success=True,
            data={"images": ["https://example.com/out.png"]},
            provider="google",
            model="gemini-2.0-flash-image-exp",
        )
    )

    result = await generate_storyboard_image_urls(
        prompt="test prompt",
        refs=[
            "http://backend.local/uploads/ref-1.png",
            "http://backend.local/uploads/ref-2.png",
        ],
        model="google:gemini-2.0-flash-image-exp",
        count=1,
        size="1024x1024",
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
    assert kwargs["prefer_provider"] == "google"
    assert kwargs["model"] == "gemini-2.0-flash-image-exp"
    assert kwargs["reference_images"] == [
        "http://backend.local/uploads/ref-1.png",
        "http://backend.local/uploads/ref-2.png",
    ]
    assert "image_url" not in kwargs
    assert result["image_gen"]["mode"] == "text_to_image"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_storyboard_codex_overload_falls_back_to_seedream():
    overloaded = "Our servers are currently overloaded. Please try again later."
    image = "https://example.com/fallback.png"
    model_id = "doubao-seedream-4-5-251128"
    ai_service = _DummyAIService(
        [
            _DummyResponse(success=False, data={}, provider="codex", model="gpt-image-2", error=overloaded),
            _DummyResponse(success=True, data={"images": [image]}, provider="volcengine", model=model_id),
        ]
    )

    result = await generate_storyboard_image_urls(
        prompt="test prompt",
        refs=["http://backend.local/uploads/ref-1.png"],
        model="codex:gpt-image-2",
        count=1, size="1536x1536", aspect_ratio="1:1", width=None, height=None,
        style="realistic", style_preset_id=None, style_spec=None,
        ai_service=ai_service,
        backend_base="http://backend.local",
    )

    calls = [(kwargs["prefer_provider"], kwargs["model"]) for _, kwargs in ai_service.ai_manager.calls]
    assert calls == [("codex", "gpt-image-2"), ("volcengine", model_id)]
    assert result["urls"] == [image]
    assert result["provider"] == "volcengine"
    assert result["image_gen"]["model_id"] == model_id
    assert result["image_gen"]["fallback_from_model"] == "codex:gpt-image-2"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_storyboard_strength_forces_image_to_image_even_when_provider_supports_reference_images():
    ai_service = _DummyAIService(
        _DummyResponse(
            success=True,
            data={"images": ["https://example.com/out.png"]},
            provider="google",
            model="gemini-2.0-flash-image-exp",
        )
    )

    await generate_storyboard_image_urls(
        prompt="test prompt",
        refs=[
            "http://backend.local/uploads/ref-1.png",
            "http://backend.local/uploads/ref-2.png",
        ],
        model="google:gemini-2.0-flash-image-exp",
        count=1,
        size="1024x1024",
        aspect_ratio="1:1",
        width=1024,
        height=1024,
        style="realistic",
        style_preset_id=None,
        style_spec=None,
        strength=0.5,
        ai_service=ai_service,
        backend_base="http://backend.local",
    )

    method, kwargs = ai_service.ai_manager.last_call or ("", {})
    assert method == "image_to_image"
    assert kwargs["image_url"] == "http://backend.local/uploads/ref-1.png"
    assert kwargs["extra_images"] == ["http://backend.local/uploads/ref-2.png"]
