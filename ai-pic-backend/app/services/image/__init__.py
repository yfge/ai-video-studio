"""
Image generation service package.

Provides services for AI-powered image generation including:
- Virtual IP portrait and scene generation
- Image persistence (local and OSS)
- Provider-specific generation (DALL-E, Keling, Stability)
"""

from app.services.image.image_generation_service import (
    ImageGenerationService,
    get_image_generation_service,
)

__all__ = ["ImageGenerationService", "get_image_generation_service"]
