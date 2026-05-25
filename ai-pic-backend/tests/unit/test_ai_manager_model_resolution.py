from types import SimpleNamespace

import pytest
from app.services import ai_manager_model_resolution as model_resolution
from app.services.providers.base import AIModelType, ModelInfo


def _model(model_id: str, model_type: AIModelType) -> ModelInfo:
    return ModelInfo(
        model_id=model_id,
        name=model_id,
        description=model_id,
        model_type=model_type,
    )


@pytest.mark.asyncio
async def test_resolve_text_model_prefers_requested_model():
    provider = SimpleNamespace(available_models=[], default_model="default-text")

    async def _fetch(_provider, _model_type):  # noqa: ANN001
        raise AssertionError("fetch should not be called")

    assert (
        await model_resolution.resolve_text_model(provider, "explicit", _fetch)
        == "explicit"
    )


@pytest.mark.asyncio
async def test_resolve_image_model_prefers_static_model():
    provider = SimpleNamespace(
        available_models=[_model("static-image", AIModelType.TEXT_TO_IMAGE)],
        default_model="default-image",
    )

    async def _fetch(_provider, _model_type):  # noqa: ANN001
        return [_model("remote-image", AIModelType.TEXT_TO_IMAGE)]

    resolved = await model_resolution.resolve_image_model(provider, None, _fetch)

    assert resolved == "static-image"


@pytest.mark.asyncio
async def test_resolve_image_to_image_model_falls_back_to_text_to_image():
    provider = SimpleNamespace(available_models=[], default_model="default-image")

    async def _fetch(_provider, model_type):  # noqa: ANN001
        if model_type == AIModelType.TEXT_TO_IMAGE:
            return [_model("remote-text-image", AIModelType.TEXT_TO_IMAGE)]
        return []

    resolved = await model_resolution.resolve_image_to_image_model(
        provider,
        None,
        _fetch,
    )

    assert resolved == "remote-text-image"


@pytest.mark.asyncio
async def test_resolve_video_model_uses_text_to_video_static_for_image_to_video():
    provider = SimpleNamespace(
        available_models=[_model("static-text-video", AIModelType.TEXT_TO_VIDEO)],
        default_model="default-video",
    )

    async def _fetch(_provider, _model_type):  # noqa: ANN001
        return []

    resolved = await model_resolution.resolve_video_model(
        provider,
        None,
        AIModelType.IMAGE_TO_VIDEO,
        _fetch,
    )

    assert resolved == "static-text-video"


@pytest.mark.asyncio
async def test_resolve_video_model_uses_provider_default_last():
    provider = SimpleNamespace(available_models=[], default_model="default-video")

    async def _fetch(_provider, _model_type):  # noqa: ANN001
        return []

    resolved = await model_resolution.resolve_video_model(
        provider,
        None,
        AIModelType.TEXT_TO_VIDEO,
        _fetch,
    )

    assert resolved == "default-video"
