from types import SimpleNamespace

import pytest
from app.services import ai_manager_image_fallback as image_fallback
from app.services.providers.base import AIModelType, AIResponse, AITaskType


def _logger():
    return SimpleNamespace(
        warning=lambda *_args, **_kwargs: None,
        error=lambda *_args, **_kwargs: None,
    )


def test_infer_image_provider_from_model():
    assert image_fallback.infer_image_provider_from_model("seedream-4") == "volcengine"
    assert image_fallback.infer_image_provider_from_model("kling-v2") == "keling"
    assert image_fallback.infer_image_provider_from_model("gpt-image-1") == "openai"
    assert image_fallback.infer_image_provider_from_model("gemini-2.5") == "google"
    assert image_fallback.infer_image_provider_from_model("unknown") is None


@pytest.mark.asyncio
async def test_fallback_image_to_image_as_text_to_image_success():
    captured_kwargs = {}

    async def _generate_image(**kwargs):
        captured_kwargs.update(kwargs)
        return AIResponse(
            success=True,
            data={"images": ["https://cdn.example.com/a.png"]},
            provider="openai",
            model="gpt-image-1",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
            metadata={"existing": "value"},
        )

    result = await image_fallback.fallback_image_to_image_as_text_to_image(
        _generate_image,
        prompt=None,
        model="gpt-image-1",
        prefer_provider=None,
        image_url="https://example.com/ref.png",
        count=2,
        legacy_style="cartoon",
        style_preset_id=None,
        style_spec=None,
        logger=_logger(),
    )

    assert result.response is not None
    assert captured_kwargs["prefer_provider"] == "openai"
    assert captured_kwargs["n"] == 2
    assert result.response.model_type == AIModelType.IMAGE_TO_IMAGE
    assert result.response.task_type == AITaskType.SCENE_GENERATION
    assert result.response.metadata["fallback_from"] == "image_to_image"
    assert result.response.metadata["existing"] == "value"


@pytest.mark.asyncio
async def test_fallback_image_to_image_as_text_to_image_failure():
    async def _generate_image(**_kwargs):
        return AIResponse(
            success=False,
            error="",
            provider="google",
            model="gemini",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )

    result = await image_fallback.fallback_image_to_image_as_text_to_image(
        _generate_image,
        prompt="draw",
        model="gemini",
        prefer_provider=None,
        image_url="https://example.com/ref.png",
        count=None,
        legacy_style="realistic",
        style_preset_id=None,
        style_spec=None,
        logger=_logger(),
    )

    assert result.response is None
    assert result.last_error == "未知错误"
    assert result.last_provider == "google"
    assert result.last_model == "gemini"
