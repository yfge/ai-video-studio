"""Unit tests for ImageGenerationService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.image.image_generation_service import (
    ImageGenerationService,
    get_image_generation_service,
)


class TestImageGenerationService:
    """Tests for ImageGenerationService class."""

    def test_init_without_ai_manager(self):
        """Test service initialization without AI manager."""
        service = ImageGenerationService()
        assert service.ai_manager is None
        assert service.logger is not None

    def test_init_with_ai_manager(self):
        """Test service initialization with AI manager."""
        mock_manager = MagicMock()
        service = ImageGenerationService(ai_manager=mock_manager)
        assert service.ai_manager is mock_manager

    def test_is_keling_model(self):
        """Test Keling model detection."""
        service = ImageGenerationService()
        assert service._is_keling_model("keling-image") is True
        assert service._is_keling_model("kling-v1") is True
        assert service._is_keling_model("keling") is True
        assert service._is_keling_model("kling") is True
        assert service._is_keling_model("dall-e-3") is False
        assert service._is_keling_model("openai") is False

    def test_is_dalle_model(self):
        """Test DALL-E model detection."""
        service = ImageGenerationService()
        assert service._is_dalle_model("dall-e-3") is True
        assert service._is_dalle_model("dalle-3") is True
        assert service._is_dalle_model("dall-e-2") is True
        assert service._is_dalle_model("keling") is False
        assert service._is_dalle_model("openai") is False

    def test_build_prompt_portrait(self):
        """Test prompt building for portrait category."""
        service = ImageGenerationService()
        prompt = service._build_prompt(
            ip_name="TestIP",
            description="A friendly character",
            style="realistic",
            category="portrait",
            additional_prompts=None,
        )
        assert "portrait" in prompt
        assert "TestIP" in prompt
        assert "friendly character" in prompt
        assert "realistic" in prompt

    def test_build_prompt_scene(self):
        """Test prompt building for scene category."""
        service = ImageGenerationService()
        prompt = service._build_prompt(
            ip_name="TestIP",
            description="A magical world",
            style="anime",
            category="scene",
            additional_prompts=None,
        )
        assert "scene" in prompt
        assert "TestIP" in prompt
        assert "magical world" in prompt
        assert "anime" in prompt

    def test_build_prompt_with_additional(self):
        """Test prompt building with additional prompts."""
        service = ImageGenerationService()
        prompt = service._build_prompt(
            ip_name="TestIP",
            description="A character",
            style="realistic",
            category="portrait",
            additional_prompts=["high quality", "detailed"],
        )
        assert "high quality" in prompt
        assert "detailed" in prompt

    def test_resolve_style_default(self):
        """Test style resolution with default values."""
        service = ImageGenerationService()
        result = service._resolve_style(
            style="realistic",
            style_preset_id=None,
            style_spec=None,
        )
        resolved_spec, resolution, derived, style_prompt, openai_style = result
        assert resolved_spec is None
        assert derived == "realistic"
        assert openai_style == "natural"

    def test_resolve_style_vivid(self):
        """Test style resolution with vivid style."""
        service = ImageGenerationService()
        result = service._resolve_style(
            style="anime",
            style_preset_id=None,
            style_spec=None,
        )
        resolved_spec, resolution, derived, style_prompt, openai_style = result
        assert derived == "anime"
        assert openai_style == "vivid"


class TestGetImageGenerationService:
    """Tests for get_image_generation_service factory function."""

    def test_get_service_creates_singleton(self):
        """Test that factory creates singleton instance."""
        # Reset global state
        import app.services.image.image_generation_service as module
        module._image_generation_service = None

        service1 = get_image_generation_service()
        service2 = get_image_generation_service()
        assert service1 is service2

    def test_get_service_with_manager(self):
        """Test that factory accepts AI manager on first call."""
        import app.services.image.image_generation_service as module
        module._image_generation_service = None

        mock_manager = MagicMock()
        service = get_image_generation_service(ai_manager=mock_manager)
        assert service.ai_manager is mock_manager


class TestGenerateVirtualIPImage:
    """Tests for generate_virtual_ip_image method."""

    @pytest.mark.asyncio
    async def test_generate_with_dalle(self):
        """Test image generation with DALL-E."""
        service = ImageGenerationService()

        with patch(
            "app.services.image.image_generation_service.generate_with_openai_dalle"
        ) as mock_dalle:
            with patch(
                "app.services.image.image_generation_service.persist_generated_image"
            ) as mock_persist:
                mock_dalle.return_value = "https://example.com/image.png"
                mock_persist.return_value = {
                    "local_file_path": "/tmp/image.png",
                    "relative_path": "/uploads/image.png",
                    "file_size": 1024,
                    "filename": "image.png",
                    "oss_url": "https://cdn.example.com/image.png",
                }

                result = await service.generate_virtual_ip_image(
                    ip_name="TestIP",
                    description="A character",
                    model="dall-e-3",
                )

                assert result is not None
                assert result["model_used"] == "dall-e-3"
                assert result["generation_method"] == "openai_dalle"
                mock_dalle.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_keling(self):
        """Test image generation with Keling AI."""
        mock_manager = AsyncMock()
        service = ImageGenerationService(ai_manager=mock_manager)

        with patch(
            "app.services.image.image_generation_service.generate_with_keling"
        ) as mock_keling:
            with patch(
                "app.services.image.image_generation_service.persist_generated_image"
            ) as mock_persist:
                mock_keling.return_value = "https://example.com/keling.png"
                mock_persist.return_value = {
                    "local_file_path": "/tmp/keling.png",
                    "relative_path": "/uploads/keling.png",
                    "file_size": 2048,
                    "filename": "keling.png",
                    "oss_url": "https://cdn.example.com/keling.png",
                }

                result = await service.generate_virtual_ip_image(
                    ip_name="TestIP",
                    description="A character",
                    model="keling-image",
                )

                assert result is not None
                assert result["model_used"] == "keling-image"
                assert result["generation_method"] == "keling_image"
                mock_keling.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_returns_none_on_failure(self):
        """Test that generation returns None when provider fails."""
        service = ImageGenerationService()

        with patch(
            "app.services.image.image_generation_service.generate_with_openai_dalle"
        ) as mock_dalle:
            mock_dalle.return_value = None

            result = await service.generate_virtual_ip_image(
                ip_name="TestIP",
                description="A character",
                model="dall-e-3",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_generate_handles_persistence_error(self):
        """Test that generation handles persistence errors gracefully."""
        service = ImageGenerationService()

        with patch(
            "app.services.image.image_generation_service.generate_with_openai_dalle"
        ) as mock_dalle:
            with patch(
                "app.services.image.image_generation_service.persist_generated_image"
            ) as mock_persist:
                mock_dalle.return_value = "https://example.com/image.png"
                mock_persist.side_effect = Exception("Upload failed")

                result = await service.generate_virtual_ip_image(
                    ip_name="TestIP",
                    description="A character",
                    model="dall-e-3",
                )

                assert result is None
