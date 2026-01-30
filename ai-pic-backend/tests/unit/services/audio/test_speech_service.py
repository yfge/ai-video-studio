"""Unit tests for SpeechService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.audio.speech_service import SpeechService, get_speech_service


class TestSpeechService:
    """Tests for SpeechService class."""

    def test_init_without_ai_manager(self):
        """Test service initialization without AI manager."""
        service = SpeechService()
        assert service.ai_manager is None
        assert service.logger is not None

    def test_init_with_ai_manager(self):
        """Test service initialization with AI manager."""
        mock_manager = MagicMock()
        service = SpeechService(ai_manager=mock_manager)
        assert service.ai_manager is mock_manager

    def test_get_oss_url_or_original_with_success(self):
        """Test URL extraction when OSS upload succeeds."""
        oss_result = {"success": True, "file_url": "https://cdn.example.com/audio.mp3"}
        result = SpeechService._get_oss_url_or_original(
            oss_result, "https://original.example.com/audio.mp3"
        )
        assert result == "https://cdn.example.com/audio.mp3"

    def test_get_oss_url_or_original_with_failure(self):
        """Test URL extraction when OSS upload fails."""
        oss_result = {"success": False}
        result = SpeechService._get_oss_url_or_original(
            oss_result, "https://original.example.com/audio.mp3"
        )
        assert result == "https://original.example.com/audio.mp3"

    def test_get_oss_url_or_original_with_none(self):
        """Test URL extraction when OSS result is None."""
        result = SpeechService._get_oss_url_or_original(
            None, "https://original.example.com/audio.mp3"
        )
        assert result == "https://original.example.com/audio.mp3"


class TestGetSpeechService:
    """Tests for get_speech_service factory function."""

    def test_get_service_creates_singleton(self):
        """Test that factory creates singleton instance."""
        # Reset global state
        import app.services.audio.speech_service as module

        module._speech_service = None

        service1 = get_speech_service()
        service2 = get_speech_service()
        assert service1 is service2

    def test_get_service_with_manager(self):
        """Test that factory accepts AI manager on first call."""
        import app.services.audio.speech_service as module

        module._speech_service = None

        mock_manager = MagicMock()
        service = get_speech_service(ai_manager=mock_manager)
        assert service.ai_manager is mock_manager


class TestGenerateSpeech:
    """Tests for generate_speech method."""

    @pytest.mark.asyncio
    async def test_generate_without_ai_manager(self):
        """Test generation fails without AI manager."""
        service = SpeechService()

        result = await service.generate_speech(
            text="Hello, world!",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful speech generation."""
        mock_manager = AsyncMock()
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.provider = "minimax"
        mock_response.model = "speech-model"
        mock_response.metadata = {}
        mock_response.data = {
            "audio_url": "https://provider.example.com/audio.mp3",
            "duration": 2.5,
        }
        mock_manager.text_to_speech.return_value = mock_response

        service = SpeechService(ai_manager=mock_manager)

        with patch("app.services.audio.speech_service.oss_service", None):
            result = await service.generate_speech(
                text="Hello, world!",
                voice_type="female_1",
                speed=1.0,
            )

        assert result is not None
        assert result["audio_url"] == "https://provider.example.com/audio.mp3"
        assert result["provider_used"] == "minimax"
        assert result["text"] == "Hello, world!"
        assert result["voice_type"] == "female_1"
        assert result["duration"] == 2.5
        mock_manager.text_to_speech.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_failure(self):
        """Test speech generation failure."""
        mock_manager = AsyncMock()
        mock_response = MagicMock()
        mock_response.success = False
        mock_response.error = "Generation failed"
        mock_manager.text_to_speech.return_value = mock_response

        service = SpeechService(ai_manager=mock_manager)

        result = await service.generate_speech(text="Test text")

        assert result is None

    @pytest.mark.asyncio
    async def test_generate_with_exception(self):
        """Test exception handling during generation."""
        mock_manager = AsyncMock()
        mock_manager.text_to_speech.side_effect = Exception("Network error")

        service = SpeechService(ai_manager=mock_manager)

        result = await service.generate_speech(text="Test text")

        assert result is None

    @pytest.mark.asyncio
    async def test_generate_with_oss_upload(self):
        """Test generation with OSS upload."""
        mock_manager = AsyncMock()
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.provider = "minimax"
        mock_response.model = "speech-model"
        mock_response.metadata = {}
        mock_response.data = {
            "audio_url": "https://provider.example.com/audio.mp3",
            "duration": 3.0,
        }
        mock_manager.text_to_speech.return_value = mock_response

        mock_oss = MagicMock()
        mock_oss.upload_from_url = AsyncMock(
            return_value={
                "success": True,
                "file_url": "https://cdn.example.com/audio.mp3",
            }
        )

        service = SpeechService(ai_manager=mock_manager)

        with patch("app.services.audio.speech_service.oss_service", mock_oss):
            result = await service.generate_speech(text="Test text")

        assert result["audio_url"] == "https://cdn.example.com/audio.mp3"
        assert result["original_audio_url"] == "https://provider.example.com/audio.mp3"

    @pytest.mark.asyncio
    async def test_generate_with_provider_preference(self):
        """Test generation with provider preference."""
        mock_manager = AsyncMock()
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.provider = "aliyun"
        mock_response.model = "aliyun-tts"
        mock_response.metadata = {}
        mock_response.data = {"audio_url": "https://example.com/audio.mp3"}
        mock_manager.text_to_speech.return_value = mock_response

        service = SpeechService(ai_manager=mock_manager)

        with patch("app.services.audio.speech_service.oss_service", None):
            await service.generate_speech(
                text="Test",
                prefer_provider="aliyun",
            )

        # Check that prefer_provider was passed
        call_kwargs = mock_manager.text_to_speech.call_args[1]
        assert call_kwargs.get("prefer_provider") == "aliyun"


class TestOSSUploadMethod:
    """Tests for OSS upload helper method."""

    @pytest.mark.asyncio
    async def test_upload_audio_to_oss_success(self):
        """Test successful audio OSS upload."""
        mock_oss = MagicMock()
        mock_oss.upload_from_url = AsyncMock(
            return_value={
                "success": True,
                "file_url": "https://cdn.example.com/audio.mp3",
            }
        )

        service = SpeechService()

        with patch("app.services.audio.speech_service.oss_service", mock_oss):
            result = await service._upload_audio_to_oss(
                audio_url="https://example.com/audio.mp3",
                text="Hello world",
                voice_type="female_1",
                speed=1.0,
                provider="minimax",
                model="speech-model",
            )

        assert result["success"] is True
        assert result["file_url"] == "https://cdn.example.com/audio.mp3"

    @pytest.mark.asyncio
    async def test_upload_audio_to_oss_no_url(self):
        """Test OSS upload with no audio URL."""
        service = SpeechService()

        result = await service._upload_audio_to_oss(
            audio_url=None,
            text="Hello",
            voice_type="default",
            speed=1.0,
            provider="minimax",
            model="tts",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_upload_audio_to_oss_no_service(self):
        """Test OSS upload with no OSS service."""
        service = SpeechService()

        with patch("app.services.audio.speech_service.oss_service", None):
            result = await service._upload_audio_to_oss(
                audio_url="https://example.com/audio.mp3",
                text="Hello",
                voice_type="default",
                speed=1.0,
                provider="minimax",
                model="tts",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_upload_audio_truncates_long_text(self):
        """Test that long text is truncated in OSS metadata."""
        mock_oss = MagicMock()
        mock_oss.upload_from_url = AsyncMock(
            return_value={
                "success": True,
                "file_url": "https://cdn.example.com/audio.mp3",
            }
        )

        service = SpeechService()
        long_text = "A" * 200

        with patch("app.services.audio.speech_service.oss_service", mock_oss):
            await service._upload_audio_to_oss(
                audio_url="https://example.com/audio.mp3",
                text=long_text,
                voice_type="default",
                speed=1.0,
                provider="minimax",
                model="tts",
            )

        # Check that text was truncated in metadata
        call_kwargs = mock_oss.upload_from_url.call_args[1]
        metadata_text = call_kwargs["metadata"]["text"]
        assert len(metadata_text) == 103  # 100 chars + "..."
        assert metadata_text.endswith("...")
