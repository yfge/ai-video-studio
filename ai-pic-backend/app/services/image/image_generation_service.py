"""
Image generation service.

Provides unified interface for AI-powered image generation,
supporting multiple providers (DALL-E, Keling, Volcengine, etc.).
"""

from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.services.image.image_persistence import persist_generated_image
from app.services.image.image_providers import (
    generate_with_keling,
    generate_with_openai_dalle,
)
from app.services.storage import oss_service
from app.utils.model_utils import parse_model_and_provider


class ImageGenerationService:
    """Service for AI-powered image generation."""

    def __init__(self, ai_manager=None):
        """
        Initialize image generation service.

        Args:
            ai_manager: Optional AIServiceManager instance for multi-provider support.
        """
        self.logger = get_logger()
        self.ai_manager = ai_manager
        self.openai_api_key = settings.OPENAI_API_KEY
        self.stability_api_key = settings.STABILITY_API_KEY
        self.base_url = settings.AI_SERVICE_URL
        self.api_key = settings.AI_API_KEY

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
        """
        Generate image for a virtual IP character.

        Args:
            ip_name: Name of the virtual IP character.
            description: Character description.
            style: Image style (realistic, anime, etc.).
            style_preset_id: Optional style preset ID.
            style_spec: Optional style specification object.
            category: Image category (portrait, scene, etc.).
            model: Model to use for generation.
            additional_prompts: Additional prompt modifiers.
            background_story: Character background story.
            count: Number of images to generate.
            size: Image size specification.
            aspect_ratio: Image aspect ratio.

        Returns:
            Dictionary with generation results including URLs and metadata.
        """
        raw_model = model or "dalle-3"
        pure_model, provider_hint = parse_model_and_provider(raw_model)
        pure_model = pure_model or "dall-e-3"

        # Resolve style specification
        resolved_style_spec, style_spec_resolution, derived_style, style_prompt, openai_style = (
            self._resolve_style(style, style_preset_id, style_spec)
        )

        # Build the prompt
        final_prompt = self._build_prompt(
            ip_name, description, derived_style, category, additional_prompts
        )
        direct_prompt = f"{final_prompt}\n\n{style_prompt}" if style_prompt else final_prompt

        self.logger.info(f"Image generation prompt: {final_prompt[:200]}...")
        self.logger.info(
            "Using model: %s (provider_hint=%s), style: %s, category: %s",
            pure_model, provider_hint, derived_style, category,
        )

        # Generate image using appropriate provider
        image_url, provider_used, generation_method = await self._generate_image(
            prompt=final_prompt,
            direct_prompt=direct_prompt,
            pure_model=pure_model,
            provider_hint=provider_hint,
            derived_style=derived_style,
            openai_style=openai_style,
            category=category,
            size=size,
            aspect_ratio=aspect_ratio,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
            count=count,
        )

        if not image_url:
            return None

        # Persist the generated image
        try:
            stored = await persist_generated_image(
                image_url,
                ip_name=ip_name,
                category=category,
                prefix="ai-generated/virtual-ip",
                metadata={
                    "ip_name": ip_name,
                    "style": derived_style,
                    "category": category,
                    "style_preset_id": (style_preset_id or "").strip() or None,
                    "style_spec": (
                        resolved_style_spec.model_dump(mode="json", exclude_none=True)
                        if resolved_style_spec is not None
                        else None
                    ),
                    "style_spec_resolution": style_spec_resolution,
                    "aspect_ratio": aspect_ratio,
                    "provider": provider_used,
                    "model": model,
                },
                require_upload=bool(oss_service),
            )
        except Exception as exc:
            self.logger.error(f"Image save/upload failed: {exc}")
            return None

        return {
            "prompt": final_prompt,
            "style": derived_style,
            "model_used": pure_model,
            "generation_method": generation_method,
            "original_image_url": image_url,
            "usage": {},
            "style_preset_id": style_preset_id,
            "style_spec": (
                resolved_style_spec.model_dump(mode="json", exclude_none=True)
                if resolved_style_spec is not None
                else None
            ),
            "style_spec_resolution": style_spec_resolution,
            **stored,
        }

    def _resolve_style(
        self,
        style: str,
        style_preset_id: str | None,
        style_spec: Any | None,
    ) -> tuple:
        """Resolve style specification to concrete style parameters."""
        resolved_style_spec = None
        style_spec_resolution: dict[str, Any] | None = None
        derived_style = style
        style_prompt = ""
        openai_style = "natural" if style == "realistic" else "vivid"

        try:
            if style_preset_id or style_spec is not None:
                from app.utils.style_utils import (
                    build_style_prompt,
                    derive_legacy_image_style,
                    derive_openai_image_style,
                    resolve_style_spec,
                )

                resolved_style_spec, style_spec_resolution = resolve_style_spec(
                    style_spec=style_spec,
                    style_preset_id=style_preset_id,
                    legacy_style=style,
                    fill_defaults=True,
                )
                derived_style = derive_legacy_image_style(resolved_style_spec)
                style_prompt = build_style_prompt(resolved_style_spec)
                openai_style = derive_openai_image_style(
                    resolved_style_spec, fallback=derived_style
                )
        except Exception as exc:
            resolved_style_spec = None
            style_spec_resolution = {"error": str(exc)}
            derived_style = style
            style_prompt = ""
            openai_style = "natural" if style == "realistic" else "vivid"

        return resolved_style_spec, style_spec_resolution, derived_style, style_prompt, openai_style

    def _build_prompt(
        self,
        ip_name: str,
        description: str,
        style: str,
        category: str,
        additional_prompts: List[str] | None,
    ) -> str:
        """Build the generation prompt for virtual IP image."""
        if category == "portrait":
            final_prompt = f"A professional {style} portrait of {ip_name}, {description}"
        else:
            final_prompt = f"A professional {style} {category} of {ip_name}, {description}"

        if additional_prompts:
            final_prompt += f", {', '.join(additional_prompts)}"

        return final_prompt

    async def _generate_image(
        self,
        prompt: str,
        direct_prompt: str,
        pure_model: str,
        provider_hint: str | None,
        derived_style: str,
        openai_style: str,
        category: str,
        size: str | None,
        aspect_ratio: str | None,
        style_preset_id: str | None,
        style_spec: Any | None,
        count: int,
    ) -> tuple[Optional[str], str, str]:
        """Generate image using appropriate provider."""
        provider_used = "openai"
        generation_method = "openai_dalle"
        image_url = None

        normalized_model = pure_model.lower()

        if self._is_keling_model(normalized_model):
            image_url = await generate_with_keling(
                self.ai_manager,
                prompt, derived_style, category, pure_model,
                style_preset_id=style_preset_id,
                style_spec=style_spec,
                aspect_ratio=aspect_ratio,
            )
            provider_used = "keling"
            generation_method = "keling_image"

        elif self._is_dalle_model(normalized_model):
            image_url = await generate_with_openai_dalle(
                direct_prompt, openai_style, category, size=size or "1024x1024"
            )
            provider_used = "openai"
            generation_method = "openai_dalle"

        elif self.ai_manager:
            image_url, provider_used, generation_method = await self._generate_with_manager(
                prompt, pure_model, normalized_model, provider_hint, derived_style,
                style_preset_id, style_spec, size, aspect_ratio, count
            )

        else:
            image_url = await generate_with_openai_dalle(
                direct_prompt, openai_style, category
            )
            provider_used = "openai"
            generation_method = "openai_dalle"

        return image_url, provider_used, generation_method

    def _is_keling_model(self, model: str) -> bool:
        """Check if model is a Keling model."""
        return (
            model.startswith("keling-") or
            model.startswith("kling-") or
            model in {"keling", "kling"}
        )

    def _is_dalle_model(self, model: str) -> bool:
        """Check if model is a DALL-E model."""
        return model.startswith("dall-e") or model.startswith("dalle")

    async def _generate_with_manager(
        self,
        prompt: str,
        pure_model: str,
        normalized_model: str,
        provider_hint: str | None,
        derived_style: str,
        style_preset_id: str | None,
        style_spec: Any | None,
        size: str | None,
        aspect_ratio: str | None,
        count: int,
    ) -> tuple[Optional[str], str, str]:
        """Generate image using AI service manager."""
        prefer_provider = provider_hint

        if normalized_model.startswith("seedream") or normalized_model.startswith("volcengine"):
            prefer_provider = "volcengine"
        elif normalized_model.startswith("deepseek"):
            prefer_provider = "deepseek"
        elif normalized_model.startswith("google"):
            prefer_provider = "google"

        response = await self.ai_manager.generate_image(
            prompt=prompt,
            width=1024,
            height=1024,
            style=derived_style,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
            model=pure_model,
            n=count or 1,
            prefer_provider=prefer_provider,
            size=size if prefer_provider == "volcengine" else size,
            aspect_ratio=aspect_ratio,
        )

        if response.success:
            images = response.data.get("images", [])
            image_url = images[0] if images else None
            provider_used = response.provider or "unknown"
            generation_method = f"ai_{provider_used}"
            return image_url, provider_used, generation_method
        else:
            self.logger.error(f"AI manager image generation failed: {response.error}")
            return None, "unknown", "ai_failed"


# Global service instance (lazy initialization)
_image_generation_service: Optional[ImageGenerationService] = None


def get_image_generation_service(ai_manager=None) -> ImageGenerationService:
    """
    Get or create the image generation service instance.

    Args:
        ai_manager: Optional AIServiceManager to use. If provided on first call,
                    will be used to initialize the service.

    Returns:
        ImageGenerationService instance.
    """
    global _image_generation_service
    if _image_generation_service is None:
        _image_generation_service = ImageGenerationService(ai_manager=ai_manager)
    return _image_generation_service
