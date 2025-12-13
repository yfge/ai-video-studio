import pytest

from app.core.logging import get_logger
from app.services.ai_service_manager import (
    AIServiceConfig,
    AIServiceManager,
    ProviderWeight,
)
from app.services.providers.base import (
    AIModelType,
    AITaskType,
    AIResponse,
    BaseProvider,
    ModelInfo,
    ProviderConfig,
)


class _RecordingProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.last_generate_image_call: dict | None = None

    @property
    def supported_model_types(self):
        return [AIModelType.TEXT_TO_IMAGE]

    @property
    def available_models(self):
        return [
            ModelInfo(
                model_id="dall-e-3",
                name="stub",
                description="stub",
                model_type=AIModelType.TEXT_TO_IMAGE,
                capabilities=["text_to_image"],
            )
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
        self.last_generate_image_call = {"prompt": prompt, "model": model, **kwargs}
        return AIResponse(
            success=True,
            data={"images": ["stub://image"]},
            provider=self.name,
            model=model or "unused",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
            metadata={},
        )


def _build_manager_with_recording_openai_provider() -> AIServiceManager:
    config = AIServiceConfig(
        providers={"openai": ProviderConfig(name="openai")},
        provider_weights={"openai": ProviderWeight(provider_name="openai")},
        enable_fallback=False,
        enable_load_balancing=False,
        max_retries=1,
    )
    manager = AIServiceManager.__new__(AIServiceManager)
    manager.config = config
    manager.providers = {}
    manager.provider_classes = {"openai": _RecordingProvider}
    manager._initialize_providers()
    manager.logger = get_logger()
    return manager


@pytest.mark.asyncio
async def test_generate_image_injects_style_spec_prompt_and_metadata():
    manager = _build_manager_with_recording_openai_provider()
    provider = manager.providers["openai"]
    assert isinstance(provider, _RecordingProvider)

    resp = await manager.generate_image(
        prompt="A test prompt",
        prefer_provider="openai",
        style="realistic",
        style_preset_id="cyberpunk_neon",
        style_spec={"color_mood": "monochrome"},
    )

    assert resp.success is True
    assert provider.last_generate_image_call is not None
    assert "STYLE_SPEC =>" in provider.last_generate_image_call["prompt"]
    assert provider.last_generate_image_call["style"] == "natural"

    assert isinstance(resp.metadata.get("style_spec"), dict)
    assert resp.metadata["style_spec"]["style_universe"] == "cyberpunk"
    assert resp.metadata["style_spec"]["color_mood"] == "monochrome"
    assert resp.metadata["style_spec_resolution"]["preset_id"] == "cyberpunk_neon"
