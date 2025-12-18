"""Unit tests for VideoGenerationService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.video.video_generation_service import (
    VideoGenerationService,
    get_video_generation_service,
)


class TestVideoGenerationService:
    """Tests for VideoGenerationService class."""

    def test_init_without_ai_manager(self):
        """Test service initialization without AI manager."""
        service = VideoGenerationService()
        assert service.ai_manager is None
        assert service.logger is not None

    def test_init_with_ai_manager(self):
        """Test service initialization with AI manager."""
        mock_manager = MagicMock()
        service = VideoGenerationService(ai_manager=mock_manager)
        assert service.ai_manager is mock_manager

    def test_get_oss_url_or_original_with_success(self):
        """Test URL extraction when OSS upload succeeds."""
        oss_result = {"success": True, "file_url": "https://cdn.example.com/video.mp4"}
        result = VideoGenerationService._get_oss_url_or_original(
            oss_result, "https://original.example.com/video.mp4"
        )
        assert result == "https://cdn.example.com/video.mp4"

    def test_get_oss_url_or_original_with_failure(self):
        """Test URL extraction when OSS upload fails."""
        oss_result = {"success": False}
        result = VideoGenerationService._get_oss_url_or_original(
            oss_result, "https://original.example.com/video.mp4"
        )
        assert result == "https://original.example.com/video.mp4"

    def test_get_oss_url_or_original_with_none(self):
        """Test URL extraction when OSS result is None."""
        result = VideoGenerationService._get_oss_url_or_original(
            None, "https://original.example.com/video.mp4"
        )
        assert result == "https://original.example.com/video.mp4"


class TestGetVideoGenerationService:
    """Tests for get_video_generation_service factory function."""

    def test_get_service_creates_singleton(self):
        """Test that factory creates singleton instance."""
        # Reset global state
        import app.services.video.video_generation_service as module
        module._video_generation_service = None

        service1 = get_video_generation_service()
        service2 = get_video_generation_service()
        assert service1 is service2

    def test_get_service_with_manager(self):
        """Test that factory accepts AI manager on first call."""
        import app.services.video.video_generation_service as module
        module._video_generation_service = None

        mock_manager = MagicMock()
        service = get_video_generation_service(ai_manager=mock_manager)
        assert service.ai_manager is mock_manager


class TestGenerateVideo:
    """Tests for generate_video method."""

    @pytest.mark.asyncio
    async def test_generate_without_ai_manager(self):
        """Test generation fails without AI manager."""
        service = VideoGenerationService()

        result = await service.generate_video(
            prompt="A beautiful sunset",
            duration=5,
        )

        assert result["success"] is False
        assert "AI manager" in result["error"]

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful video generation."""
        mock_manager = AsyncMock()
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.provider = "keling"
        mock_response.model = "kling-video"
        mock_response.metadata = {}
        mock_response.data = {
            "video_url": "https://provider.example.com/video.mp4",
            "thumbnail_url": "https://provider.example.com/thumb.jpg",
            "last_frame_url": "https://provider.example.com/last.jpg",
            "duration": 5,
        }
        mock_manager.generate_video.return_value = mock_response

        service = VideoGenerationService(ai_manager=mock_manager)

        with patch("app.services.video.video_generation_service.oss_service", None):
            result = await service.generate_video(
                prompt="A beautiful sunset",
                duration=5,
            )

        assert result["video_url"] == "https://provider.example.com/video.mp4"
        assert result["provider_used"] == "keling"
        assert result["model_used"] == "kling-video"
        mock_manager.generate_video.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_image_input(self):
        """Test image-to-video generation."""
        mock_manager = AsyncMock()
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.provider = "volcengine"
        mock_response.model = "jimeng-video"
        mock_response.metadata = {}
        mock_response.data = {
            "video_url": "https://provider.example.com/video.mp4",
            "duration": 10,
        }
        mock_manager.generate_video.return_value = mock_response

        service = VideoGenerationService(ai_manager=mock_manager)

        with patch("app.services.video.video_generation_service.oss_service", None):
            result = await service.generate_video(
                image_url="https://example.com/source.jpg",
                duration=10,
            )

        assert result["video_url"] == "https://provider.example.com/video.mp4"
        assert result["image_url"] == "https://example.com/source.jpg"

    @pytest.mark.asyncio
    async def test_generate_failure(self):
        """Test video generation failure."""
        mock_manager = AsyncMock()
        mock_response = MagicMock()
        mock_response.success = False
        mock_response.error = "Generation failed"
        mock_response.provider = "keling"
        mock_response.model = "kling-video"
        mock_response.metadata = {}
        mock_manager.generate_video.return_value = mock_response

        service = VideoGenerationService(ai_manager=mock_manager)

        result = await service.generate_video(prompt="Test prompt")

        assert result["success"] is False
        assert result["error"] == "Generation failed"
        assert result["provider_used"] == "keling"

    @pytest.mark.asyncio
    async def test_generate_with_exception(self):
        """Test exception handling during generation."""
        mock_manager = AsyncMock()
        mock_manager.generate_video.side_effect = Exception("Network error")

        service = VideoGenerationService(ai_manager=mock_manager)

        result = await service.generate_video(prompt="Test prompt")

        assert result["success"] is False
        assert "Network error" in result["error"]

    @pytest.mark.asyncio
    async def test_generate_with_oss_upload(self):
        """Test generation with OSS upload."""
        mock_manager = AsyncMock()
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.provider = "keling"
        mock_response.model = "kling-video"
        mock_response.metadata = {}
        mock_response.data = {
            "video_url": "https://provider.example.com/video.mp4",
            "thumbnail_url": "https://provider.example.com/thumb.jpg",
            "last_frame_url": "https://provider.example.com/last.jpg",
            "duration": 5,
        }
        mock_manager.generate_video.return_value = mock_response

        mock_oss = MagicMock()
        mock_oss.upload_from_url = AsyncMock(return_value={
            "success": True,
            "file_url": "https://cdn.example.com/video.mp4",
        })

        service = VideoGenerationService(ai_manager=mock_manager)

        with patch("app.services.video.video_generation_service.oss_service", mock_oss):
            result = await service.generate_video(prompt="Test prompt")

        assert result["video_url"] == "https://cdn.example.com/video.mp4"
        assert result["original_video_url"] == "https://provider.example.com/video.mp4"

    @pytest.mark.asyncio
    async def test_default_return_last_frame(self):
        """Test that return_last_frame defaults to True."""
        mock_manager = AsyncMock()
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.provider = "keling"
        mock_response.model = "kling-video"
        mock_response.metadata = {}
        mock_response.data = {"video_url": "https://example.com/video.mp4"}
        mock_manager.generate_video.return_value = mock_response

        service = VideoGenerationService(ai_manager=mock_manager)

        with patch("app.services.video.video_generation_service.oss_service", None):
            await service.generate_video(prompt="Test")

        # Check that return_last_frame was passed as True
        call_kwargs = mock_manager.generate_video.call_args[1]
        assert call_kwargs.get("return_last_frame") is True


class TestOSSUploadMethods:
    """Tests for OSS upload helper methods."""

    @pytest.mark.asyncio
    async def test_upload_video_to_oss_success(self):
        """Test successful video OSS upload."""
        mock_oss = MagicMock()
        mock_oss.upload_from_url = AsyncMock(return_value={
            "success": True,
            "file_url": "https://cdn.example.com/video.mp4",
        })

        service = VideoGenerationService()

        with patch("app.services.video.video_generation_service.oss_service", mock_oss):
            result = await service._upload_video_to_oss(
                video_url="https://example.com/video.mp4",
                prompt="Test prompt",
                duration=5,
                fps=24,
                resolution="1280x720",
                end_image_url=None,
                provider="keling",
                model="kling-video",
            )

        assert result["success"] is True
        assert result["file_url"] == "https://cdn.example.com/video.mp4"

    @pytest.mark.asyncio
    async def test_upload_video_to_oss_no_url(self):
        """Test OSS upload with no video URL."""
        service = VideoGenerationService()

        result = await service._upload_video_to_oss(
            video_url=None,
            prompt="Test",
            duration=5,
            fps=24,
            resolution="1280x720",
            end_image_url=None,
            provider="keling",
            model="kling-video",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_upload_video_to_oss_no_service(self):
        """Test OSS upload with no OSS service."""
        service = VideoGenerationService()

        with patch("app.services.video.video_generation_service.oss_service", None):
            result = await service._upload_video_to_oss(
                video_url="https://example.com/video.mp4",
                prompt="Test",
                duration=5,
                fps=24,
                resolution="1280x720",
                end_image_url=None,
                provider="keling",
                model="kling-video",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_upload_thumbnail_to_oss_success(self):
        """Test successful thumbnail OSS upload."""
        mock_oss = MagicMock()
        mock_oss.upload_from_url = AsyncMock(return_value={
            "success": True,
            "file_url": "https://cdn.example.com/thumb.jpg",
        })

        service = VideoGenerationService()

        with patch("app.services.video.video_generation_service.oss_service", mock_oss):
            result = await service._upload_thumbnail_to_oss(
                thumbnail_url="https://example.com/thumb.jpg",
                prompt="Test prompt",
                provider="keling",
            )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_upload_last_frame_to_oss_success(self):
        """Test successful last frame OSS upload."""
        mock_oss = MagicMock()
        mock_oss.upload_from_url = AsyncMock(return_value={
            "success": True,
            "file_url": "https://cdn.example.com/last.jpg",
        })

        service = VideoGenerationService()

        with patch("app.services.video.video_generation_service.oss_service", mock_oss):
            result = await service._upload_last_frame_to_oss(
                last_frame_url="https://example.com/last.jpg",
                prompt="Test prompt",
                provider="keling",
            )

        assert result["success"] is True
