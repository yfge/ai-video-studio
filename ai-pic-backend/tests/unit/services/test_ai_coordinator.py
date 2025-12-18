"""Unit tests for AIServiceCoordinator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ai_coordinator import (
    AIServiceCoordinator,
    get_ai_coordinator,
)


class TestAIServiceCoordinator:
    """Tests for AIServiceCoordinator class."""

    def test_init_without_ai_manager(self):
        """Test coordinator initialization without AI manager."""
        coordinator = AIServiceCoordinator()
        assert coordinator.ai_manager is None
        assert coordinator._image_service is not None
        assert coordinator._video_service is not None
        assert coordinator._speech_service is not None

    def test_init_with_ai_manager(self):
        """Test coordinator initialization with AI manager."""
        mock_manager = MagicMock()
        coordinator = AIServiceCoordinator(ai_manager=mock_manager)
        assert coordinator.ai_manager is mock_manager

    def test_get_ai_providers_status_without_manager(self):
        """Test provider status returns empty without manager."""
        coordinator = AIServiceCoordinator()
        result = coordinator.get_ai_providers_status()
        assert result == {}

    def test_get_ai_providers_status_with_manager(self):
        """Test provider status delegates to manager."""
        mock_manager = MagicMock()
        mock_manager.get_provider_status.return_value = {"openai": "active"}
        coordinator = AIServiceCoordinator(ai_manager=mock_manager)

        result = coordinator.get_ai_providers_status()

        assert result == {"openai": "active"}
        mock_manager.get_provider_status.assert_called_once()


class TestGetAICoordinator:
    """Tests for get_ai_coordinator factory function."""

    def test_get_coordinator_creates_singleton(self):
        """Test that factory creates singleton instance."""
        import app.services.ai_coordinator as module
        module._ai_coordinator = None

        coordinator1 = get_ai_coordinator()
        coordinator2 = get_ai_coordinator()
        assert coordinator1 is coordinator2

    def test_get_coordinator_with_manager(self):
        """Test that factory accepts AI manager on first call."""
        import app.services.ai_coordinator as module
        module._ai_coordinator = None

        mock_manager = MagicMock()
        coordinator = get_ai_coordinator(ai_manager=mock_manager)
        assert coordinator.ai_manager is mock_manager


class TestGenerateVirtualIPImage:
    """Tests for image generation delegation."""

    @pytest.mark.asyncio
    async def test_delegates_to_image_service(self):
        """Test image generation delegates to image service."""
        coordinator = AIServiceCoordinator()
        coordinator._image_service.generate_virtual_ip_image = AsyncMock(
            return_value={"image_url": "https://example.com/image.png"}
        )

        result = await coordinator.generate_virtual_ip_image(
            ip_name="TestIP",
            description="A character",
            model="dall-e-3",
        )

        assert result["image_url"] == "https://example.com/image.png"
        coordinator._image_service.generate_virtual_ip_image.assert_called_once()


class TestGenerateVideo:
    """Tests for video generation delegation."""

    @pytest.mark.asyncio
    async def test_delegates_to_video_service(self):
        """Test video generation delegates to video service."""
        coordinator = AIServiceCoordinator()
        coordinator._video_service.generate_video = AsyncMock(
            return_value={"video_url": "https://example.com/video.mp4"}
        )

        result = await coordinator.generate_video(
            prompt="A beautiful sunset",
            duration=5,
        )

        assert result["video_url"] == "https://example.com/video.mp4"
        coordinator._video_service.generate_video.assert_called_once()


class TestGenerateSpeech:
    """Tests for speech generation delegation."""

    @pytest.mark.asyncio
    async def test_delegates_to_speech_service(self):
        """Test speech generation delegates to speech service."""
        coordinator = AIServiceCoordinator()
        coordinator._speech_service.generate_speech = AsyncMock(
            return_value={"audio_url": "https://example.com/audio.mp3"}
        )

        result = await coordinator.generate_speech(
            text="Hello, world!",
            voice_type="female_1",
        )

        assert result["audio_url"] == "https://example.com/audio.mp3"
        coordinator._speech_service.generate_speech.assert_called_once()


class TestListModels:
    """Tests for model listing."""

    @pytest.mark.asyncio
    async def test_list_models_without_manager(self):
        """Test list_models returns empty without manager."""
        coordinator = AIServiceCoordinator()

        result = await coordinator.list_models()

        assert result == []

    @pytest.mark.asyncio
    async def test_list_models_with_manager(self):
        """Test list_models delegates to manager."""
        mock_manager = AsyncMock()
        mock_manager.list_models.return_value = [
            {"id": "dall-e-3", "type": "text_to_image", "provider": "openai"}
        ]
        coordinator = AIServiceCoordinator(ai_manager=mock_manager)

        result = await coordinator.list_models(model_type_alias="image")

        assert len(result) == 1
        assert result[0]["id"] == "dall-e-3"

    @pytest.mark.asyncio
    async def test_list_models_uses_cache(self):
        """Test list_models uses cache on subsequent calls."""
        mock_manager = AsyncMock()
        mock_manager.list_models.return_value = [
            {"id": "dall-e-3", "type": "text_to_image", "provider": "openai"}
        ]
        coordinator = AIServiceCoordinator(ai_manager=mock_manager)

        # First call
        await coordinator.list_models(model_type_alias="image")
        # Second call should use cache
        await coordinator.list_models(model_type_alias="image")

        # Manager should only be called once
        assert mock_manager.list_models.call_count == 1


class TestApplyUIMetadata:
    """Tests for UI metadata application."""

    def test_apply_video_ui_metadata(self):
        """Test UI metadata for video models."""
        model = {
            "id": "kling-video",
            "type": "image_to_video",
            "provider": "keling",
            "capabilities": ["720p", "1080p", "5s", "10s"],
        }

        result = AIServiceCoordinator._apply_ui_metadata(model)

        assert "metadata" in result
        assert "ui" in result["metadata"]
        ui = result["metadata"]["ui"]
        assert "resolution_options" in ui
        assert "duration_options" in ui

    def test_apply_image_ui_metadata(self):
        """Test UI metadata for image models."""
        model = {
            "id": "dall-e-3",
            "type": "text_to_image",
            "provider": "openai",
            "capabilities": [],
        }

        result = AIServiceCoordinator._apply_ui_metadata(model)

        assert "metadata" in result
        assert "ui" in result["metadata"]
        ui = result["metadata"]["ui"]
        assert "size_options" in ui

    def test_apply_ui_metadata_preserves_existing(self):
        """Test that existing UI metadata is preserved."""
        model = {
            "id": "custom-model",
            "type": "image_to_video",
            "provider": "custom",
            "capabilities": [],
            "metadata": {
                "ui": {"custom_option": True}
            }
        }

        result = AIServiceCoordinator._apply_ui_metadata(model)

        ui = result["metadata"]["ui"]
        assert ui.get("custom_option") is True

    def test_apply_ui_metadata_handles_unknown_type(self):
        """Test UI metadata handling for unknown model types."""
        model = {
            "id": "unknown-model",
            "type": "unknown_type",
            "provider": "unknown",
            "capabilities": [],
        }

        result = AIServiceCoordinator._apply_ui_metadata(model)

        # Should return model without error
        assert result["id"] == "unknown-model"
