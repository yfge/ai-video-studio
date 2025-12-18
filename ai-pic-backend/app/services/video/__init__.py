"""
Video generation service package.

Provides services for AI-powered video generation including:
- Text-to-video and image-to-video generation
- Video persistence and OSS upload
- Provider-specific generation (Keling, Volcengine, MiniMax)
"""

from app.services.video.video_generation_service import (
    VideoGenerationService,
    get_video_generation_service,
)

__all__ = ["VideoGenerationService", "get_video_generation_service"]
