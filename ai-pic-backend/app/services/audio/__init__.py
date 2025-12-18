"""
Audio generation service package.

Provides services for AI-powered audio generation including:
- Text-to-speech synthesis
- Audio persistence and OSS upload
"""

from app.services.audio.speech_service import (
    SpeechService,
    get_speech_service,
)

__all__ = ["SpeechService", "get_speech_service"]
