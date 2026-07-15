"""
Video generation service.

Provides unified interface for AI-powered video generation,
supporting multiple providers (Keling, Volcengine, MiniMax, etc.).
"""

from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.services.video.video_upload_pipeline import upload_video_with_optional_trim
from app.services.video.video_upload_utils import (
    get_oss_url_or_original,
    upload_video_last_frame_to_oss,
    upload_video_thumbnail_to_oss,
)


class VideoGenerationService:
    """Service for AI-powered video generation."""

    def __init__(self, ai_manager=None):
        """
        Initialize video generation service.

        Args:
            ai_manager: Optional AIServiceManager instance for multi-provider support.
        """
        self.logger = get_logger()
        self.ai_manager = ai_manager

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
        """
        Generate video using AI providers.

        Args:
            prompt: Text prompt for text-to-video generation.
            image_url: Source image URL for image-to-video generation.
            end_image_url: Optional end frame image URL.
            model: Model to use for generation.
            duration: Video duration in seconds.
            fps: Frames per second.
            resolution: Video resolution (e.g., "1280x720").
            style: Video style.
            prefer_provider: Preferred AI provider.
            **kwargs: Additional provider-specific options.

        Returns:
            Dictionary with video URL, metadata, and OSS upload results.
        """
        if not self.ai_manager:
            return {
                "success": False,
                "error": "AI manager not initialized, cannot generate video",
            }

        try:
            # Default to returning last frame for video chaining
            if "return_last_frame" not in kwargs:
                kwargs["return_last_frame"] = True

            response = await self.ai_manager.generate_video(
                prompt=prompt,
                image_url=image_url,
                end_image_url=end_image_url,
                model=model,
                duration=duration,
                fps=fps,
                resolution=resolution,
                prefer_provider=prefer_provider,
                **kwargs,
            )

            if response.success:
                return await self._process_successful_response(
                    response=response,
                    prompt=prompt,
                    image_url=image_url,
                    end_image_url=end_image_url,
                    duration=duration,
                    fps=fps,
                    resolution=resolution,
                )

            return {
                "success": False,
                "error": response.error or "Video generation failed",
                "provider_used": response.provider,
                "model_used": response.model,
                "metadata": response.metadata,
            }

        except Exception as e:
            self.logger.error(f"Video generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _process_successful_response(
        self,
        response,
        prompt: str,
        image_url: str,
        end_image_url: str,
        duration: int,
        fps: int,
        resolution: str,
        target_duration_seconds: float | None = None,
    ) -> Dict[str, Any]:
        """Process successful video generation response with OSS uploads."""
        original_video_url = response.data.get("video_url")
        original_thumbnail_url = response.data.get("thumbnail_url")
        original_last_frame_url = response.data.get("last_frame_url")
        video_bytes_base64 = response.data.get("video_bytes_base64")
        video_mime_type = response.data.get("video_mime_type")
        video_download_url = response.data.get("download_url") or original_video_url
        provider_duration_seconds = int(response.data.get("duration") or duration or 0)

        video_result = await upload_video_with_optional_trim(
            original_video_url=original_video_url,
            video_download_url=video_download_url,
            video_bytes_base64=video_bytes_base64,
            video_mime_type=video_mime_type,
            prompt=prompt,
            end_image_url=end_image_url,
            provider=response.provider,
            model=response.model,
            fps=fps,
            resolution=resolution,
            provider_duration_seconds=provider_duration_seconds or duration,
            target_duration_seconds=target_duration_seconds,
            logger=self.logger,
        )
        thumbnail_oss_result = await upload_video_thumbnail_to_oss(
            thumbnail_url=original_thumbnail_url,
            prompt=prompt,
            provider=response.provider,
            logger=self.logger,
        )
        last_frame_oss_result = video_result.pop("trimmed_last_frame_oss_upload", None)
        if not (last_frame_oss_result or {}).get("success"):
            last_frame_oss_result = await upload_video_last_frame_to_oss(
                last_frame_url=original_last_frame_url,
                prompt=prompt,
                provider=response.provider,
                logger=self.logger,
            )

        return {
            **video_result,
            "thumbnail_url": get_oss_url_or_original(
                thumbnail_oss_result, original_thumbnail_url
            ),
            "original_video_url": original_video_url,
            "original_thumbnail_url": original_thumbnail_url,
            "last_frame_url": get_oss_url_or_original(
                last_frame_oss_result, original_last_frame_url
            ),
            "original_last_frame_url": original_last_frame_url,
            "thumbnail_oss_upload": thumbnail_oss_result,
            "last_frame_oss_upload": last_frame_oss_result,
            "prompt": prompt,
            "image_url": image_url,
            "end_image_url": end_image_url,
            "generation_method": f"ai_{response.provider}",
            "provider_used": response.provider,
            "model_used": response.model,
            "metadata": response.metadata,
        }


# Global service instance (lazy initialization)
_video_generation_service: Optional[VideoGenerationService] = None


def get_video_generation_service(ai_manager=None) -> VideoGenerationService:
    """
    Get or create the video generation service instance.

    Args:
        ai_manager: Optional AIServiceManager to use.

    Returns:
        VideoGenerationService instance.
    """
    global _video_generation_service
    if _video_generation_service is None:
        _video_generation_service = VideoGenerationService(ai_manager=ai_manager)
    return _video_generation_service
