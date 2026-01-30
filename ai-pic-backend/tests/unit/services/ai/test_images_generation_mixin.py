from unittest.mock import AsyncMock, MagicMock

import pytest
from app.core.config import settings
from app.prompts.manager import prompt_manager
from app.services.ai.images_generation import ImageGenerationMixin


class _DummyResponse:
    def __init__(
        self,
        *,
        success: bool,
        data: dict,
        provider: str | None = None,
        model: str | None = None,
        error: str | None = None,
    ) -> None:
        self.success = success
        self.data = data
        self.provider = provider
        self.model = model
        self.error = error


class _DummyManager:
    def __init__(self, response: _DummyResponse) -> None:
        self._response = response
        self.last_kwargs: dict | None = None

    async def generate_image(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class _DummyService(ImageGenerationMixin):
    def __init__(self, *, ai_manager=None) -> None:
        self.ai_manager = ai_manager
        self.logger = MagicMock()
        self._generate_with_openai_dalle = AsyncMock()
        self._persist_generated_image = AsyncMock(
            return_value={
                "local_file_path": "/tmp/out.png",
                "relative_path": "/uploads/out.png",
                "file_size": 123,
                "filename": "out.png",
                "oss_url": None,
                "oss_upload": None,
            }
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_virtual_ip_text_to_image_openai_normalizes_size(monkeypatch):
    service = _DummyService()
    monkeypatch.setattr(prompt_manager, "render_prompt", lambda *_args, **_kwargs: "P0")

    service._generate_with_openai_dalle.return_value = "data:image/png;base64,AAA"

    result = await service.generate_virtual_ip_image(
        ip_name="TestIP",
        description="desc",
        model="dalle-3",
        size="2K",
        style_preset_id="realistic_cinematic",
        style_spec={"style_universe": "japanese_anime"},
    )

    assert result is not None
    assert result["model_used"] == "dall-e-3"
    assert result["size"] == "1024x1024"
    assert result["width"] == 1024
    assert result["height"] == 1024

    (prompt_arg, *_), kwargs = service._generate_with_openai_dalle.call_args
    assert prompt_arg.count("STYLE_SPEC =>") == 1
    assert kwargs["size"] == "1024x1024"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_virtual_ip_text_to_image_ai_manager_uses_base_prompt(monkeypatch):
    manager = _DummyManager(
        _DummyResponse(
            success=True,
            data={"images": ["https://example.com/out.png"]},
            provider="volcengine",
            model="doubao-seedream-4-5-251128",
        )
    )
    service = _DummyService(ai_manager=manager)
    monkeypatch.setattr(prompt_manager, "render_prompt", lambda *_args, **_kwargs: "P0")

    result = await service.generate_virtual_ip_image(
        ip_name="TestIP",
        description="desc",
        model="volcengine:doubao-seedream-4-5-251128",
        size="2K",
        count=2,
        style_spec={"style_universe": "japanese_anime"},
    )

    assert manager.last_kwargs is not None
    assert manager.last_kwargs["prompt"] == "P0"
    assert "STYLE_SPEC =>" not in manager.last_kwargs["prompt"]
    assert manager.last_kwargs["prefer_provider"] == "volcengine"
    assert manager.last_kwargs["model"] == "doubao-seedream-4-5-251128"
    assert manager.last_kwargs["n"] == 2
    assert manager.last_kwargs["size"] == "2K"
    assert "width" not in manager.last_kwargs
    assert "height" not in manager.last_kwargs

    assert result is not None
    assert result["model_used"] == "doubao-seedream-4-5-251128"
    assert result["provider_used"] == "volcengine"
    assert "STYLE_SPEC =>" in result["prompt"]
    assert result["size"] == "2K"
    assert result["width"] == 2048
    assert result["height"] == 2048


@pytest.mark.unit
@pytest.mark.asyncio
async def test_virtual_ip_text_to_image_ai_manager_passes_reference_images(monkeypatch):
    manager = _DummyManager(
        _DummyResponse(
            success=True,
            data={"images": ["https://example.com/out.png"]},
            provider="google",
            model="gemini-2.0-flash-image-exp",
        )
    )
    service = _DummyService(ai_manager=manager)
    monkeypatch.setattr(prompt_manager, "render_prompt", lambda *_args, **_kwargs: "P0")

    result = await service.generate_virtual_ip_image(
        ip_name="TestIP",
        description="desc",
        model="google:gemini-2.0-flash-image-exp",
        reference_images=["/uploads/ref.png"],
    )

    assert manager.last_kwargs is not None
    backend_base = (
        getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
    ).rstrip("/")
    assert manager.last_kwargs["reference_images"] == [
        f"{backend_base}/uploads/ref.png"
    ]

    assert result is not None
    assert result["provider_used"] == "google"
