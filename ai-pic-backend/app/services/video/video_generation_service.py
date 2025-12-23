"""
Video generation service.

Provides unified interface for AI-powered video generation,
supporting multiple providers (Keling, Volcengine, MiniMax, etc.).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.storage import oss_service


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
    ) -> Dict[str, Any]:
        """Process successful video generation response with OSS uploads."""
        original_video_url = response.data.get("video_url")
        original_thumbnail_url = response.data.get("thumbnail_url")
        original_last_frame_url = response.data.get("last_frame_url")
        video_download_url = response.data.get("download_url") or original_video_url

        # Upload assets to OSS
        video_oss_result = await self._upload_video_to_oss(
            video_download_url, prompt, duration, fps, resolution,
            end_image_url, response.provider, response.model
        )
        thumbnail_oss_result = await self._upload_thumbnail_to_oss(
            original_thumbnail_url, prompt, response.provider
        )
        last_frame_oss_result = await self._upload_last_frame_to_oss(
            original_last_frame_url, prompt, response.provider
        )

        return {
            "video_url": self._get_oss_url_or_original(video_oss_result, original_video_url),
            "thumbnail_url": self._get_oss_url_or_original(thumbnail_oss_result, original_thumbnail_url),
            "original_video_url": original_video_url,
            "original_thumbnail_url": original_thumbnail_url,
            "last_frame_url": self._get_oss_url_or_original(last_frame_oss_result, original_last_frame_url),
            "original_last_frame_url": original_last_frame_url,
            "video_oss_upload": video_oss_result,
            "thumbnail_oss_upload": thumbnail_oss_result,
            "last_frame_oss_upload": last_frame_oss_result,
            "duration": response.data.get("duration", duration),
            "prompt": prompt,
            "image_url": image_url,
            "end_image_url": end_image_url,
            "generation_method": f"ai_{response.provider}",
            "provider_used": response.provider,
            "model_used": response.model,
            "metadata": response.metadata,
        }

    async def _upload_video_to_oss(
        self,
        video_url: str,
        prompt: str,
        duration: int,
        fps: int,
        resolution: str,
        end_image_url: str,
        provider: str,
        model: str,
    ) -> Optional[Dict[str, Any]]:
        """Upload video to OSS with metadata."""
        if not video_url or not oss_service:
            return None

        try:
            return await oss_service.upload_from_url(
                url=video_url,
                file_type="video",
                prefix="ai-generated/videos",
                metadata={
                    "prompt": prompt or "image_to_video",
                    "duration": str(duration),
                    "fps": str(fps),
                    "resolution": resolution,
                    "end_image_url": end_image_url or "",
                    "provider": provider,
                    "model": model,
                    "generation_time": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            self.logger.warning(f"Video OSS upload failed: {e}")
            return None

    async def _upload_thumbnail_to_oss(
        self,
        thumbnail_url: str,
        prompt: str,
        provider: str,
    ) -> Optional[Dict[str, Any]]:
        """Upload thumbnail to OSS."""
        if not thumbnail_url or not oss_service:
            return None

        try:
            return await oss_service.upload_from_url(
                url=thumbnail_url,
                file_type="image",
                prefix="ai-generated/thumbnails",
                metadata={
                    "type": "video_thumbnail",
                    "prompt": prompt or "image_to_video",
                    "provider": provider,
                    "generation_time": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            self.logger.warning(f"Thumbnail OSS upload failed: {e}")
            return None

    async def _upload_last_frame_to_oss(
        self,
        last_frame_url: str,
        prompt: str,
        provider: str,
    ) -> Optional[Dict[str, Any]]:
        """Upload video last frame to OSS."""
        if not last_frame_url or not oss_service:
            return None

        try:
            return await oss_service.upload_from_url(
                url=last_frame_url,
                file_type="image",
                prefix="ai-generated/video-last-frames",
                metadata={
                    "type": "video_last_frame",
                    "prompt": prompt or "image_to_video",
                    "provider": provider,
                    "generation_time": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            self.logger.warning(f"Last frame OSS upload failed: {e}")
            return None

    @staticmethod
    def _get_oss_url_or_original(
        oss_result: Optional[Dict[str, Any]],
        original_url: str,
    ) -> Optional[str]:
        """Get OSS URL if available, otherwise return original."""
        if oss_result and oss_result.get("success"):
            return oss_result.get("file_url")
        return original_url


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
