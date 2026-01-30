import pytest
from app.api.v1 import ai_providers
from app.core.logging import get_logger
from app.services.ai_service_manager import (
    AIServiceConfig,
    AIServiceManager,
    ProviderWeight,
)
from app.services.providers.base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
    ModelInfo,
    ProviderConfig,
)
from fastapi import HTTPException


class _DummyProvider(BaseProvider):
    """Minimal provider stub for list_models tests."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = None

    @property
    def supported_model_types(self):
        return [
            AIModelType.TEXT_TO_IMAGE,
            AIModelType.IMAGE_TO_IMAGE,
            AIModelType.TEXT_TO_VIDEO,
        ]

    @property
    def available_models(self):
        return [
            ModelInfo(
                model_id="img-capable",
                name="Img2Img capable",
                description="Text2img model that also supports variations",
                model_type=AIModelType.TEXT_TO_IMAGE,
                capabilities=["text_to_image", "image_to_image"],
            ),
            ModelInfo(
                model_id="img-direct",
                name="Native img2img",
                description="Image-to-image native model",
                model_type=AIModelType.IMAGE_TO_IMAGE,
                capabilities=["image_to_image"],
            ),
            ModelInfo(
                model_id="img-only",
                name="Plain text2img",
                description="Text-to-image only",
                model_type=AIModelType.TEXT_TO_IMAGE,
                capabilities=["text_to_image"],
            ),
            ModelInfo(
                model_id="vid-capable",
                name="Video model w/ i2v",
                description="Text-to-video model that also supports image-to-video",
                model_type=AIModelType.TEXT_TO_VIDEO,
                capabilities=["text_to_video", "image_to_video"],
            ),
        ]

    async def _initialize_client(self):
        self._client = object()

    async def generate_text(self, prompt: str, model: str = None, **kwargs):
        return AIResponse(
            success=False,
            error="not-used",
            provider=self.name,
            model=model or "unused",
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )

    async def generate_image(self, prompt: str, model: str = None, **kwargs):
        return AIResponse(
            success=True,
            data={"images": []},
            provider=self.name,
            model=model or "unused",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )


def _build_manager_with_dummy_provider():
    config = AIServiceConfig(
        providers={"dummy": ProviderConfig(name="dummy")},
        provider_weights={"dummy": ProviderWeight(provider_name="dummy")},
    )
    manager = AIServiceManager.__new__(AIServiceManager)
    manager.config = config
    manager.providers = {}
    manager.provider_classes = {"dummy": _DummyProvider}
    manager._initialize_providers()
    manager.logger = get_logger()
    return manager


@pytest.mark.asyncio
async def test_list_models_accepts_image_to_image_capability():
    manager = _build_manager_with_dummy_provider()

    models = await manager.list_models(
        model_type=AIModelType.IMAGE_TO_IMAGE, source="static"
    )

    ids = {m["id"] for m in models}
    assert "img-capable" in ids  # capability-based inclusion
    assert "img-direct" in ids  # native IMAGE_TO_IMAGE type
    assert "img-only" not in ids


@pytest.mark.asyncio
async def test_list_models_accepts_image_to_video_capability():
    manager = _build_manager_with_dummy_provider()

    models = await manager.list_models(
        model_type=AIModelType.IMAGE_TO_VIDEO, source="static"
    )

    ids = {m["id"] for m in models}
    assert "vid-capable" in ids


@pytest.mark.asyncio
async def test_available_models_route_propagates_http_exception(monkeypatch):
    class _StubAIService:
        def get_ai_providers_status(self):
            return {}

        async def list_models(self, model_type_alias=None, source="auto"):
            return []

    monkeypatch.setattr(ai_providers, "ai_service", _StubAIService())

    with pytest.raises(HTTPException) as excinfo:
        await ai_providers.get_available_models(current_user=object())

    assert excinfo.value.status_code == 503
