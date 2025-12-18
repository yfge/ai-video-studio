"""Unit tests for video UI utilities."""

import pytest

from app.services.video.video_ui_utils import (
    compute_video_ui,
    compute_image_ui,
)


class TestComputeVideoUI:
    """Tests for compute_video_ui function."""

    def test_empty_capabilities(self):
        """Test UI computation with no capabilities."""
        result = compute_video_ui(
            provider="unknown",
            model_id="test-model",
            caps=[],
        )

        assert "resolution_options" in result
        assert "duration_options" in result
        assert "ratio_options" in result
        assert result["default_watermark"] is False

    def test_parse_resolution_from_caps(self):
        """Test resolution parsing from capabilities."""
        result = compute_video_ui(
            provider="unknown",
            model_id="test-model",
            caps=["720p", "1080p", "4K"],
        )

        assert "720P" in result["resolution_options"]
        assert "1080P" in result["resolution_options"]

    def test_parse_duration_from_caps(self):
        """Test duration parsing from capabilities."""
        result = compute_video_ui(
            provider="unknown",
            model_id="test-model",
            caps=["5s", "10s", "30s"],
        )

        assert 5 in result["duration_options"]
        assert 10 in result["duration_options"]
        assert 30 in result["duration_options"]

    def test_keling_provider_defaults(self):
        """Test Keling provider defaults."""
        result = compute_video_ui(
            provider="keling",
            model_id="kling-video",
            caps=[],
        )

        assert result["supports_end_frame"] is True
        assert result["supports_camera_control"] is True
        assert result["supports_watermark"] is False
        assert "1080P" in result["resolution_options"]
        assert "720P" in result["resolution_options"]
        assert 5 in result["duration_options"]
        assert 10 in result["duration_options"]

    def test_volcengine_provider_defaults(self):
        """Test Volcengine provider defaults."""
        result = compute_video_ui(
            provider="volcengine",
            model_id="jimeng-video",
            caps=[],
        )

        assert result["supports_watermark"] is True
        assert "480P" in result["resolution_options"]
        assert "720P" in result["resolution_options"]
        assert "1080P" in result["resolution_options"]
        assert 2 in result["duration_options"]
        assert 12 in result["duration_options"]

    def test_volcengine_with_end_frame_cap(self):
        """Test Volcengine with end frame capability."""
        result = compute_video_ui(
            provider="volcengine",
            model_id="jimeng-video",
            caps=["image_to_video_start_end_frame"],
        )

        assert result["supports_end_frame"] is True

    def test_minimax_provider_defaults(self):
        """Test MiniMax provider defaults."""
        result = compute_video_ui(
            provider="minimax",
            model_id="minimax-video",
            caps=[],
        )

        assert result["supports_watermark"] is True
        assert 6 in result["duration_options"]
        assert 10 in result["duration_options"]

    def test_minimax_with_caps(self):
        """Test MiniMax with resolution capabilities."""
        result = compute_video_ui(
            provider="minimax",
            model_id="minimax-video",
            caps=["720p", "1080p", "first_last_frame", "camera_control"],
        )

        assert "720P" in result["resolution_options"]
        assert "1080P" in result["resolution_options"]
        assert result["supports_end_frame"] is True
        assert result["supports_camera_control"] is True
        assert result["supports_camera_fixed"] is True

    def test_camera_control_detection(self):
        """Test camera control capability detection."""
        result = compute_video_ui(
            provider="unknown",
            model_id="test-model",
            caps=["camera_control"],
        )

        assert result["supports_camera_control"] is True

    def test_end_frame_detection(self):
        """Test end frame capability detection."""
        # Test with start_end_frame capability
        result1 = compute_video_ui(
            provider="unknown",
            model_id="test-model",
            caps=["image_to_video_start_end_frame"],
        )
        assert result1["supports_end_frame"] is True

        # Test with first_last_frame capability
        result2 = compute_video_ui(
            provider="unknown",
            model_id="test-model",
            caps=["first_last_frame"],
        )
        assert result2["supports_end_frame"] is True

    def test_default_values(self):
        """Test default values are set correctly."""
        result = compute_video_ui(
            provider="unknown",
            model_id="test-model",
            caps=[],
        )

        assert result["default_watermark"] is False
        assert result["default_ratio"] == "16:9"
        assert "16:9" in result["ratio_options"]
        assert "9:16" in result["ratio_options"]
        assert "1:1" in result["ratio_options"]


class TestComputeImageUI:
    """Tests for compute_image_ui function."""

    def test_openai_dalle3(self):
        """Test OpenAI DALL-E 3 UI options."""
        result = compute_image_ui(
            provider="openai",
            model_id="dall-e-3",
            caps=[],
        )

        assert "1024x1024" in result["size_options"]
        assert "1024x1792" in result["size_options"]
        assert "1792x1024" in result["size_options"]
        assert result["supports_aspect_ratio"] is False

    def test_openai_dalle2(self):
        """Test OpenAI DALL-E 2 UI options."""
        result = compute_image_ui(
            provider="openai",
            model_id="dall-e-2",
            caps=[],
        )

        assert "256x256" in result["size_options"]
        assert "512x512" in result["size_options"]
        assert "1024x1024" in result["size_options"]

    def test_volcengine_seedream(self):
        """Test Volcengine Seedream UI options."""
        result = compute_image_ui(
            provider="volcengine",
            model_id="seedream-4.5",
            caps=[],
        )

        assert "2K" in result["size_options"]

    def test_keling_image(self):
        """Test Keling image UI options."""
        result = compute_image_ui(
            provider="keling",
            model_id="kling-image",
            caps=[],
        )

        assert "2k" in result["size_options"]
        assert "1k" in result["size_options"]
        assert result["supports_aspect_ratio"] is True
        assert len(result["aspect_options"]) > 0

    def test_google_provider(self):
        """Test Google provider UI options."""
        result = compute_image_ui(
            provider="google",
            model_id="gemini-image",
            caps=[],
        )

        assert result["supports_aspect_ratio"] is True

    def test_unknown_provider(self):
        """Test unknown provider returns empty options."""
        result = compute_image_ui(
            provider="unknown",
            model_id="unknown-model",
            caps=[],
        )

        assert len(result["size_options"]) == 0
        assert result["supports_aspect_ratio"] is False
        assert result["default_size"] is None

    def test_default_size_set(self):
        """Test default size is set from options."""
        result = compute_image_ui(
            provider="openai",
            model_id="dall-e-3",
            caps=[],
        )

        assert result["default_size"] == "1024x1024"
