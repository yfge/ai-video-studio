import pytest
from app.services.providers.base import (
    AIModelType,
    AIResponse,
    AITaskType,
    ProviderConfig,
)
from app.services.providers.keling_provider import KelingProvider
from app.services.providers.keling_provider import image as keling_image


@pytest.mark.asyncio
async def test_keling_image_to_image_prefers_base64(monkeypatch):
    provider = KelingProvider(
        ProviderConfig(name="keling", api_key="test-ak", api_secret="test-sk")
    )

    async def _fake_client():
        return object()

    monkeypatch.setattr(provider, "get_client", _fake_client)

    captured: dict[str, object] = {}

    async def _fake_generate_image(**kwargs):
        captured["image"] = kwargs.get("image")
        captured["n"] = kwargs.get("n")
        return AIResponse(
            success=True,
            data={"images": ["http://example.com/out.png"]},
            provider="keling",
            model=kwargs.get("model") or "kling-image-v2",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
            metadata={"task_id": "dummy"},
        )

    monkeypatch.setattr(keling_image, "generate_image", _fake_generate_image)

    resp = await provider.image_to_image(
        image_url="http://example.com/ref.png",
        prompt="make a variation",
        model="kling-image-v1",
        n=2,
        base64_images=["data:image/png;base64,REFIMG"],
    )

    assert captured["image"] == "data:image/png;base64,REFIMG"
    assert captured["n"] == 2
    assert resp.success is True
    assert resp.model_type == AIModelType.IMAGE_TO_IMAGE
    assert resp.task_type == AITaskType.SCENE_GENERATION
    assert isinstance(resp.metadata, dict)
    assert resp.metadata.get("reference_mode") == "base64"
    assert resp.metadata.get("reference_images_count") == 1


@pytest.mark.asyncio
async def test_keling_image_to_image_falls_back_to_url(monkeypatch):
    provider = KelingProvider(
        ProviderConfig(name="keling", api_key="test-ak", api_secret="test-sk")
    )

    async def _fake_client():
        return object()

    monkeypatch.setattr(provider, "get_client", _fake_client)

    captured: dict[str, object] = {}

    async def _fake_generate_image(**kwargs):
        captured["image"] = kwargs.get("image")
        return AIResponse(
            success=True,
            data={"images": ["http://example.com/out.png"]},
            provider="keling",
            model=kwargs.get("model") or "kling-image-v2",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
            metadata={},
        )

    monkeypatch.setattr(keling_image, "generate_image", _fake_generate_image)

    resp = await provider.image_to_image(
        image_url="http://example.com/ref.png",
        prompt="make a variation",
        model="kling-image-v1",
        n=1,
    )

    assert captured["image"] == "http://example.com/ref.png"
    assert resp.success is True
    assert resp.model_type == AIModelType.IMAGE_TO_IMAGE
    assert resp.task_type == AITaskType.SCENE_GENERATION
    assert isinstance(resp.metadata, dict)
    assert resp.metadata.get("reference_mode") == "url"
