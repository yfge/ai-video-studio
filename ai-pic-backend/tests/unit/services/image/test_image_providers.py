"""Unit tests for image generation providers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.image.image_providers import (
    generate_with_custom_service,
    generate_with_keling,
    generate_with_openai_dalle,
    generate_with_stability,
)


class TestGenerateWithKeling:
    """Tests for generate_with_keling function."""

    @pytest.mark.asyncio
    async def test_generate_without_manager(self):
        """Test that generation fails without AI manager."""
        result = await generate_with_keling(
            ai_manager=None,
            prompt="Test prompt",
            style="realistic",
            category="portrait",
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful Keling generation."""
        mock_manager = AsyncMock()
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.data = {"images": ["https://keling.example.com/image.png"]}
        mock_manager.generate_image.return_value = mock_response

        result = await generate_with_keling(
            ai_manager=mock_manager,
            prompt="Test prompt",
            style="realistic",
            category="portrait",
        )

        assert result == "https://keling.example.com/image.png"
        mock_manager.generate_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_empty_response(self):
        """Test handling empty image response."""
        mock_manager = AsyncMock()
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.data = {"images": []}
        mock_manager.generate_image.return_value = mock_response

        result = await generate_with_keling(
            ai_manager=mock_manager,
            prompt="Test prompt",
            style="realistic",
            category="portrait",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_generate_failure(self):
        """Test handling failed generation."""
        mock_manager = AsyncMock()
        mock_response = MagicMock()
        mock_response.success = False
        mock_response.error = "API error"
        mock_manager.generate_image.return_value = mock_response

        result = await generate_with_keling(
            ai_manager=mock_manager,
            prompt="Test prompt",
            style="realistic",
            category="portrait",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_generate_with_exception(self):
        """Test handling exception during generation."""
        mock_manager = AsyncMock()
        mock_manager.generate_image.side_effect = Exception("Network error")

        result = await generate_with_keling(
            ai_manager=mock_manager,
            prompt="Test prompt",
            style="realistic",
            category="portrait",
        )

        assert result is None


class TestGenerateWithOpenAIDalle:
    """Tests for generate_with_openai_dalle function."""

    @pytest.mark.asyncio
    async def test_generate_without_api_key(self):
        """Test that generation fails without API key."""
        with patch("app.services.image.image_providers.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None

            result = await generate_with_openai_dalle(
                prompt="Test prompt",
                style="vivid",
                category="portrait",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_generate_success_base64(self):
        """Test successful OpenAI image generation with base64 response."""
        with patch("app.services.image.image_providers.settings") as mock_settings:
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_settings.OPENAI_API_KEY = "test-api-key"
                mock_settings.OPENAI_BASE_URL = "https://api.openai.com/v1"

                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {
                    "data": [{"b64_json": "base64imagedata"}]
                }

                mock_client = AsyncMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value.__aenter__.return_value = mock_client

                result = await generate_with_openai_dalle(
                    prompt="Test prompt",
                    style="vivid",
                    category="portrait",
                )

                assert result == "data:image/png;base64,base64imagedata"
                call_args = mock_client.post.call_args
                payload = call_args.kwargs["json"]
                assert payload["model"] == "gpt-image-2"
                assert payload["quality"] == "auto"
                assert "style" not in payload
                assert "response_format" not in payload

    @pytest.mark.asyncio
    async def test_generate_success_url(self):
        """Test successful OpenAI image generation with URL response."""
        with patch("app.services.image.image_providers.settings") as mock_settings:
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_settings.OPENAI_API_KEY = "test-api-key"
                mock_settings.OPENAI_BASE_URL = "https://api.openai.com/v1"

                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {
                    "data": [{"url": "https://openai.example.com/image.png"}]
                }

                mock_client = AsyncMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value.__aenter__.return_value = mock_client

                result = await generate_with_openai_dalle(
                    prompt="Test prompt",
                    style="natural",
                    category="portrait",
                )

                assert result == "https://openai.example.com/image.png"

    @pytest.mark.asyncio
    async def test_generate_normalizes_style(self):
        """Test that non-standard styles get normalized."""
        with patch("app.services.image.image_providers.settings") as mock_settings:
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_settings.OPENAI_API_KEY = "test-api-key"
                mock_settings.OPENAI_BASE_URL = "https://api.openai.com/v1"

                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {"data": [{"b64_json": "imagedata"}]}

                mock_client = AsyncMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value.__aenter__.return_value = mock_client

                # Test realistic -> natural
                await generate_with_openai_dalle(
                    prompt="Test",
                    style="realistic",
                    category="portrait",
                    model="dall-e-3",
                )

                call_args = mock_client.post.call_args
                assert call_args[1]["json"]["style"] == "natural"

    @pytest.mark.asyncio
    async def test_generate_maps_img_gen_2_alias(self):
        """Test that user-facing img-gen-2 alias maps to the official model ID."""
        with patch("app.services.image.image_providers.settings") as mock_settings:
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_settings.OPENAI_API_KEY = "test-api-key"
                mock_settings.OPENAI_BASE_URL = "https://api.openai.com/v1"

                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {"data": [{"b64_json": "imagedata"}]}

                mock_client = AsyncMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value.__aenter__.return_value = mock_client

                await generate_with_openai_dalle(
                    prompt="Test",
                    style="vivid",
                    category="portrait",
                    model="img-gen-2",
                )

                call_args = mock_client.post.call_args
                assert call_args.kwargs["json"]["model"] == "gpt-image-2"

    @pytest.mark.asyncio
    async def test_generate_with_exception(self):
        """Test handling exception during generation."""
        with patch("app.services.image.image_providers.settings") as mock_settings:
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_settings.OPENAI_API_KEY = "test-api-key"
                mock_settings.OPENAI_BASE_URL = "https://api.openai.com/v1"

                mock_client = AsyncMock()
                mock_client.post.side_effect = Exception("API error")
                mock_client_class.return_value.__aenter__.return_value = mock_client

                result = await generate_with_openai_dalle(
                    prompt="Test prompt",
                    style="vivid",
                    category="portrait",
                )

                assert result is None


class TestGenerateWithStability:
    """Tests for generate_with_stability function."""

    @pytest.mark.asyncio
    async def test_generate_without_api_key(self):
        """Test that generation fails without API key."""
        with patch("app.services.image.image_providers.settings") as mock_settings:
            mock_settings.STABILITY_API_KEY = None

            result = await generate_with_stability(
                prompt="Test prompt",
                style="realistic",
                category="portrait",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful Stability AI generation."""
        with patch("app.services.image.image_providers.settings") as mock_settings:
            with patch("httpx.AsyncClient") as mock_client_class:
                with patch(
                    "app.services.image.image_providers.save_base64_image"
                ) as mock_save:
                    mock_settings.STABILITY_API_KEY = "test-key"

                    mock_response = MagicMock()
                    mock_response.raise_for_status = MagicMock()
                    mock_response.json.return_value = {
                        "artifacts": [{"base64": "imagedata"}]
                    }

                    mock_client = AsyncMock()
                    mock_client.post.return_value = mock_response
                    mock_client_class.return_value.__aenter__.return_value = mock_client

                    mock_save.return_value = "/uploads/stability_image.png"

                    result = await generate_with_stability(
                        prompt="Test prompt",
                        style="realistic",
                        category="portrait",
                    )

                    assert result == "/uploads/stability_image.png"
                    mock_save.assert_called_once_with("imagedata", "stability")


class TestGenerateWithCustomService:
    """Tests for generate_with_custom_service function."""

    @pytest.mark.asyncio
    async def test_generate_without_config(self):
        """Test that generation fails without service config."""
        with patch("app.services.image.image_providers.settings") as mock_settings:
            mock_settings.AI_SERVICE_URL = None
            mock_settings.AI_API_KEY = None

            result = await generate_with_custom_service(
                prompt="Test prompt",
                style="realistic",
                category="portrait",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful custom service generation."""
        with patch("app.services.image.image_providers.settings") as mock_settings:
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_settings.AI_SERVICE_URL = "https://custom.example.com"
                mock_settings.AI_API_KEY = "custom-key"

                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {
                    "image_url": "https://custom.example.com/image.png"
                }

                mock_client = AsyncMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value.__aenter__.return_value = mock_client

                result = await generate_with_custom_service(
                    prompt="Test prompt",
                    style="realistic",
                    category="portrait",
                )

                assert result == "https://custom.example.com/image.png"

    @pytest.mark.asyncio
    async def test_generate_with_custom_url(self):
        """Test generation with explicitly provided URL."""
        with patch("app.services.image.image_providers.settings") as mock_settings:
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_settings.AI_SERVICE_URL = "https://default.example.com"
                mock_settings.AI_API_KEY = "default-key"

                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {
                    "image_url": "https://override.example.com/image.png"
                }

                mock_client = AsyncMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value.__aenter__.return_value = mock_client

                result = await generate_with_custom_service(
                    prompt="Test prompt",
                    style="realistic",
                    category="portrait",
                    base_url="https://override.example.com",
                    api_key="override-key",
                )

                assert result == "https://override.example.com/image.png"

                # Verify it used the override URL
                call_args = mock_client.post.call_args
                assert "override.example.com" in call_args[0][0]
