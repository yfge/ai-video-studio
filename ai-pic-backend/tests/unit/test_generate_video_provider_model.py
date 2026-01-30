import app.services.ai.video as video_module
import pytest
from app.core.logging import get_logger
from app.services.ai_service import AIService
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


class _DummyVideoProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = None
        self.calls = []

    @property
    def supported_model_types(self):
        return [AIModelType.TEXT_TO_VIDEO, AIModelType.IMAGE_TO_VIDEO]

    @property
    def available_models(self):
        return [
            ModelInfo(
                model_id="seedance-pro",
                name="Seedance Pro",
                description="video model",
                model_type=AIModelType.TEXT_TO_VIDEO,
                capabilities=["text_to_video", "image_to_video"],
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
        return AIResponse(
            success=False,
            error="not-used",
            provider=self.name,
            model=model or "unused",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )

    async def generate_video(self, prompt=None, image_url=None, model=None, **kwargs):
        self.calls.append(
            {
                "prompt": prompt,
                "image_url": image_url,
                "model": model,
                "kwargs": kwargs,
            }
        )
        return AIResponse(
            success=True,
            data={"video_url": "https://example.com/video.mp4"},
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=(
                AIModelType.IMAGE_TO_VIDEO if image_url else AIModelType.TEXT_TO_VIDEO
            ),
        )


def _build_manager():
    config = AIServiceConfig(
        providers={"dummy": ProviderConfig(name="dummy")},
        provider_weights={"dummy": ProviderWeight(provider_name="dummy")},
    )
    manager = AIServiceManager.__new__(AIServiceManager)
    manager.config = config
    manager.providers = {}
    manager.provider_classes = {"dummy": _DummyVideoProvider}
    manager._initialize_providers()
    manager.logger = get_logger()
    return manager


class _DummyVideoManager:
    def __init__(self, response: AIResponse):
        self.response = response
        self.calls = []

    async def generate_video(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class _DummyOSS:
    def __init__(self):
        self.calls = []

    async def upload_from_url(
        self,
        url: str,
        file_type: str = "image",
        prefix: str | None = None,
        metadata: dict | None = None,
    ):
        self.calls.append(
            {
                "url": url,
                "file_type": file_type,
                "prefix": prefix,
                "metadata": metadata,
            }
        )
        suffix = ".mp4" if file_type == "video" else ".png"
        return {
            "success": True,
            "file_url": f"https://oss.example.com/{prefix or 'root'}/file{suffix}",
        }


@pytest.mark.asyncio
async def test_generate_video_strips_provider_prefix_model():
    manager = _build_manager()

    resp = await manager.generate_video(
        prompt="hello",
        image_url="https://example.com/img.png",
        model="dummy:seedance-pro",
    )

    assert resp.success is True
    provider = manager.providers["dummy"]
    assert provider.calls[-1]["model"] == "seedance-pro"


@pytest.mark.asyncio
async def test_ai_service_generate_video_uploads_last_frame(monkeypatch):
    fake_resp = AIResponse(
        success=True,
        data={
            "video_url": "https://provider.example.com/video.mp4",
            "thumbnail_url": "https://provider.example.com/thumb.png",
            "last_frame_url": "https://provider.example.com/last.png",
            "duration": 4,
        },
        provider="dummy",
        model="dummy-model",
        task_type=AITaskType.VIDEO_GENERATION,
        model_type=AIModelType.IMAGE_TO_VIDEO,
    )
    service = AIService.__new__(AIService)
    service.logger = get_logger()
    service.ai_manager = _DummyVideoManager(fake_resp)

    dummy_oss = _DummyOSS()
    monkeypatch.setattr(video_module, "oss_service", dummy_oss, raising=False)

    result = await AIService.generate_video(
        service,
        prompt="test video",
        image_url="https://cdn.example.com/start.png",
    )

    assert result["video_url"].startswith("https://oss.example.com/ai-generated/videos")
    assert result["thumbnail_url"].startswith(
        "https://oss.example.com/ai-generated/thumbnails"
    )
    assert result["last_frame_url"].startswith(
        "https://oss.example.com/ai-generated/video-last-frames"
    )
    assert any(
        call["file_type"] == "image"
        and call["url"] == "https://provider.example.com/last.png"
        for call in dummy_oss.calls
    )
    assert len(dummy_oss.calls) == 3
    assert dummy_oss.calls[0]["file_type"] == "video"
    assert service.ai_manager.calls[0]["return_last_frame"] is True


@pytest.mark.asyncio
async def test_generate_video_default_model_falls_back_to_text_to_video():
    manager = _build_manager()

    resp = await manager.generate_video(
        prompt="hello",
        image_url="https://example.com/img.png",
        model=None,
    )

    assert resp.success is True
    provider = manager.providers["dummy"]
    assert provider.calls[-1]["model"] == "seedance-pro"
