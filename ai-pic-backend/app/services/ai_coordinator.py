"""
AI Service Coordinator.

Thin orchestration layer that delegates to specialized AI services.
This coordinator provides a unified interface while keeping the actual
implementation in focused, single-responsibility service modules.
"""

from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.providers.base import AIModelType
from app.services.audio.speech_service import SpeechService
from app.services.image.image_generation_service import ImageGenerationService
from app.services.video.video_generation_service import VideoGenerationService
from app.services.video.video_ui_utils import compute_image_ui, compute_video_ui


class AIServiceCoordinator:
    """
    Coordinator for AI generation services.

    Provides a unified interface to image, video, and audio generation
    services while delegating actual implementation to specialized modules.
    """

    def __init__(self, ai_manager=None):
        """
        Initialize the AI service coordinator.

        Args:
            ai_manager: Optional AIServiceManager for multi-provider support.
        """
        self.logger = get_logger()
        self.ai_manager = ai_manager

        # Initialize specialized services
        self._image_service = ImageGenerationService(ai_manager=ai_manager)
        self._video_service = VideoGenerationService(ai_manager=ai_manager)
        self._speech_service = SpeechService(ai_manager=ai_manager)

        # Model cache for list_models
        self.model_cache: Dict[str, List[Dict[str, Any]]] = {}

    # -------------------- Image Generation --------------------

    async def generate_virtual_ip_image(
        self,
        ip_name: str,
        description: str,
        style: str = "realistic",
        style_preset_id: str | None = None,
        style_spec: Any | None = None,
        category: str = "portrait",
        model: str = "dalle-3",
        additional_prompts: List[str] = None,
        background_story: str = None,
        count: int = 1,
        size: str | None = None,
        aspect_ratio: str | None = None,
    ) -> Optional[Dict[str, Any]]:
        """Delegate to ImageGenerationService."""
        return await self._image_service.generate_virtual_ip_image(
            ip_name=ip_name,
            description=description,
            style=style,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
            category=category,
            model=model,
            additional_prompts=additional_prompts,
            background_story=background_story,
            count=count,
            size=size,
            aspect_ratio=aspect_ratio,
        )

    # -------------------- Video Generation --------------------

    async def generate_video(
        self,
        prompt: str = None,
        image_url: str = None,
        end_image_url: str = None,
        model: str | None = None,
        duration: int = 5,
        fps: int = 24,
        resolution: str = "1280x720",
        style: str = "realistic",
        prefer_provider: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Delegate to VideoGenerationService."""
        return await self._video_service.generate_video(
            prompt=prompt,
            image_url=image_url,
            end_image_url=end_image_url,
            model=model,
            duration=duration,
            fps=fps,
            resolution=resolution,
            style=style,
            prefer_provider=prefer_provider,
            **kwargs,
        )

    # -------------------- Speech Generation --------------------

    async def generate_speech(
        self,
        text: str,
        voice_type: str = None,
        speed: float = 1.0,
        prefer_provider: str = None,
    ) -> Optional[Dict[str, Any]]:
        """Delegate to SpeechService."""
        return await self._speech_service.generate_speech(
            text=text,
            voice_type=voice_type,
            speed=speed,
            prefer_provider=prefer_provider,
        )

    # -------------------- Provider Status --------------------

    def get_ai_providers_status(self) -> Dict[str, Any]:
        """Get AI provider status from ai_manager."""
        if not self.ai_manager:
            return {}
        return self.ai_manager.get_provider_status()

    # -------------------- Model Listing --------------------

    async def list_models(
        self,
        model_type_alias: Optional[str] = None,
        source: str = "auto",
    ) -> List[Dict[str, Any]]:
        """List available AI models with UI metadata enrichment."""
        if not self.ai_manager:
            return []

        aliases = {
            "text": AIModelType.TEXT_GENERATION,
            "text_generation": AIModelType.TEXT_GENERATION,
            "image": AIModelType.TEXT_TO_IMAGE,
            "text_to_image": AIModelType.TEXT_TO_IMAGE,
            "image_to_image": AIModelType.IMAGE_TO_IMAGE,
            "img2img": AIModelType.IMAGE_TO_IMAGE,
            "image_to_video": AIModelType.IMAGE_TO_VIDEO,
            "img2vid": AIModelType.IMAGE_TO_VIDEO,
            "i2v": AIModelType.IMAGE_TO_VIDEO,
            "video": AIModelType.TEXT_TO_VIDEO,
            "text_to_video": AIModelType.TEXT_TO_VIDEO,
            "tts": AIModelType.TEXT_TO_SPEECH,
            "text_to_speech": AIModelType.TEXT_TO_SPEECH,
        }
        mt = aliases.get(model_type_alias, None)

        cache_key = "all" if mt is None else mt.value
        if source == "auto" and cache_key in self.model_cache:
            cached = self.model_cache.get(cache_key) or []
            if cached:
                return cached

        models = await self.ai_manager.list_models(model_type=mt, source=source)
        enriched: List[Dict[str, Any]] = []

        for item in models:
            try:
                enriched.append(self._apply_ui_metadata(item))
            except Exception:
                enriched.append(item)

        if source == "auto":
            try:
                self.model_cache[cache_key] = enriched or []
            except Exception:
                pass

        return enriched

    @staticmethod
    def _apply_ui_metadata(model: Dict[str, Any]) -> Dict[str, Any]:
        """Attach UI-facing defaults/options based on provider/model/capabilities."""
        provider = (model.get("provider") or "").lower()
        mid = (model.get("id") or model.get("model_id") or "").lower()
        caps = [str(c).lower() for c in model.get("capabilities") or []]
        model_type = (model.get("type") or "").lower()

        metadata = dict(model.get("metadata") or {})
        ui_meta = dict(metadata.get("ui") or {})

        if model_type == AIModelType.IMAGE_TO_VIDEO.value:
            computed = compute_video_ui(provider, mid, caps)
            ui_meta = {**computed, **ui_meta} if computed else ui_meta
        elif model_type in (
            AIModelType.TEXT_TO_IMAGE.value,
            AIModelType.IMAGE_TO_IMAGE.value,
        ):
            computed = compute_image_ui(provider, mid, caps)
            ui_meta = {**computed, **ui_meta} if computed else ui_meta

        if ui_meta:
            metadata["ui"] = ui_meta
            model["metadata"] = metadata

        return model


# Global service instance (lazy initialization)
_ai_coordinator: Optional[AIServiceCoordinator] = None


def get_ai_coordinator(ai_manager=None) -> AIServiceCoordinator:
    """
    Get or create the AI service coordinator instance.

    Args:
        ai_manager: Optional AIServiceManager to use.

    Returns:
        AIServiceCoordinator instance.
    """
    global _ai_coordinator
    if _ai_coordinator is None:
        _ai_coordinator = AIServiceCoordinator(ai_manager=ai_manager)
    return _ai_coordinator
