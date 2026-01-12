import pytest
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


class _EmptyErrorImg2ImgProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    @property
    def supported_model_types(self):
        return [AIModelType.IMAGE_TO_IMAGE, AIModelType.TEXT_TO_IMAGE]

    @property
    def available_models(self):
        return [
            ModelInfo(
                model_id="dall-e-3",
                name="stub",
                description="stub",
                model_type=AIModelType.IMAGE_TO_IMAGE,
                capabilities=["image_to_image"],
            )
        ]

    async def _initialize_client(self):  # pragma: no cover - unused
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
            success=False,
            error="",
            provider=self.name,
            model=model or "unused",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )

    async def image_to_image(
        self, image_url: str, prompt: str = None, model: str = None, **kwargs
    ):
        return AIResponse(
            success=False,
            error="",
            provider=self.name,
            model=model or "unused",
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
        )


def _build_manager(provider_name: str = "openai") -> AIServiceManager:
    config = AIServiceConfig(
        providers={provider_name: ProviderConfig(name=provider_name)},
        provider_weights={provider_name: ProviderWeight(provider_name=provider_name)},
        enable_fallback=True,
        enable_load_balancing=False,
        max_retries=1,
    )
    manager = AIServiceManager.__new__(AIServiceManager)
    manager.config = config
    manager.providers = {}
    manager.provider_classes = {provider_name: _EmptyErrorImg2ImgProvider}
    manager._initialize_providers()
    manager.logger = get_logger()
    manager._models_cache = {}
    return manager


@pytest.mark.asyncio
async def test_image_to_image_returns_provider_error_when_empty(monkeypatch):
    manager = _build_manager()

    async def _fake_generate_image(**_kwargs):  # noqa: ANN001
        return AIResponse(
            success=False,
            error="",
            provider="openai",
            model="dall-e-3",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )

    monkeypatch.setattr(manager, "generate_image", _fake_generate_image)

    resp = await manager.image_to_image(
        image_url="https://example.com/ref.png",
        prompt="test",
        model="openai:dall-e-3",
        prefer_provider="openai",
        count=1,
    )

    assert resp.success is False
    assert resp.error is not None
    assert "所有图生图提供商都失败了" not in resp.error
    assert resp.error.startswith("openai:")
