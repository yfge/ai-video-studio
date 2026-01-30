"""
Speech synthesis service.

Provides unified interface for AI-powered text-to-speech generation,
supporting multiple providers.
"""

from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.services.media import build_generation_metadata
from app.services.media import upload_from_url as upload_media_from_url
from app.services.storage import oss_service


class SpeechService:
    """Service for AI-powered speech synthesis."""

    def __init__(self, ai_manager=None):
        """
        Initialize speech service.

        Args:
            ai_manager: Optional AIServiceManager instance for multi-provider support.
        """
        self.logger = get_logger()
        self.ai_manager = ai_manager

    async def generate_speech(
        self,
        text: str,
        voice_type: str = None,
        speed: float = 1.0,
        prefer_provider: str = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate speech from text using AI providers.

        Args:
            text: Text to convert to speech.
            voice_type: Voice type/ID to use.
            speed: Speech speed multiplier.
            prefer_provider: Preferred AI provider.

        Returns:
            Dictionary with audio URL, metadata, and OSS upload results.
            Returns None on failure.
        """
        if not self.ai_manager:
            self.logger.error("AI manager not initialized, cannot generate speech")
            return None

        try:
            response = await self.ai_manager.text_to_speech(
                text=text,
                voice_type=voice_type,
                speed=speed,
                prefer_provider=prefer_provider,
            )

            if response.success:
                return await self._process_successful_response(
                    response=response,
                    text=text,
                    voice_type=voice_type,
                    speed=speed,
                )

            self.logger.error(f"Speech generation failed: {response.error}")
            return None

        except Exception as e:
            self.logger.error(f"Speech generation error: {e}")
            return None

    async def _process_successful_response(
        self,
        response,
        text: str,
        voice_type: str,
        speed: float,
    ) -> Dict[str, Any]:
        """Process successful speech generation response with OSS upload."""
        original_audio_url = response.data.get("audio_url")

        # Upload audio to OSS
        audio_oss_result = await self._upload_audio_to_oss(
            audio_url=original_audio_url,
            text=text,
            voice_type=voice_type,
            speed=speed,
            provider=response.provider,
            model=response.model,
        )

        return {
            "audio_url": self._get_oss_url_or_original(
                audio_oss_result, original_audio_url
            ),
            "original_audio_url": original_audio_url,
            "audio_oss_upload": audio_oss_result,
            "duration": response.data.get("duration"),
            "text": text,
            "voice_type": voice_type,
            "speed": speed,
            "generation_method": f"ai_{response.provider}",
            "provider_used": response.provider,
            "model_used": response.model,
            "metadata": response.metadata,
        }

    async def _upload_audio_to_oss(
        self,
        audio_url: str,
        text: str,
        voice_type: str,
        speed: float,
        provider: str,
        model: str,
    ) -> Optional[Dict[str, Any]]:
        """Upload audio to OSS with metadata."""
        service = oss_service
        if not audio_url or not service:
            return None

        try:
            # Keep previous behavior: include truncated text in OSS metadata (ASCII-only).
            truncated_text = text[:100] + "..." if len(text) > 100 else text
            return await upload_media_from_url(
                url=audio_url,
                media_type="audio",
                prefix="ai-generated/audio",
                metadata=build_generation_metadata(
                    provider=provider,
                    model=model,
                    media_type="audio",
                    extra={
                        "voice_type": voice_type or "default",
                        "speed": speed,
                        "text": truncated_text,
                        "text_len": len(text or ""),
                    },
                ),
                oss_service_override=service,
            )
        except Exception as e:
            self.logger.warning(f"Audio OSS upload failed: {e}")
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
_speech_service: Optional[SpeechService] = None


def get_speech_service(ai_manager=None) -> SpeechService:
    """
    Get or create the speech service instance.

    Args:
        ai_manager: Optional AIServiceManager to use.

    Returns:
        SpeechService instance.
    """
    global _speech_service
    if _speech_service is None:
        _speech_service = SpeechService(ai_manager=ai_manager)
    return _speech_service
