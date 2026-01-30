"""Unit tests for text generation utilities."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.audio.text_generation_utils import (
    call_text_generation_with_fallback,
    extract_text_content,
    trim_text,
)


class TestCallTextGenerationWithFallback:
    """Tests for call_text_generation_with_fallback function."""

    @pytest.mark.asyncio
    async def test_first_service_success(self):
        """Test that first successful service is used."""
        service1 = AsyncMock(return_value="Result from service 1")
        service2 = AsyncMock(return_value="Result from service 2")

        result = await call_text_generation_with_fallback(
            prompt="Test prompt",
            task_type="test",
            services=[service1, service2],
        )

        assert result == "Result from service 1"
        service1.assert_called_once()
        service2.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_on_first_failure(self):
        """Test fallback to second service when first fails."""
        service1 = AsyncMock(side_effect=Exception("Service 1 failed"))
        service2 = AsyncMock(return_value="Result from service 2")

        result = await call_text_generation_with_fallback(
            prompt="Test prompt",
            task_type="test",
            services=[service1, service2],
        )

        assert result == "Result from service 2"
        service1.assert_called_once()
        service2.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_on_none_result(self):
        """Test fallback when first service returns None."""
        service1 = AsyncMock(return_value=None)
        service2 = AsyncMock(return_value="Result from service 2")

        result = await call_text_generation_with_fallback(
            prompt="Test prompt",
            task_type="test",
            services=[service1, service2],
        )

        assert result == "Result from service 2"

    @pytest.mark.asyncio
    async def test_all_services_fail(self):
        """Test that None is returned when all services fail."""
        service1 = AsyncMock(side_effect=Exception("Service 1 failed"))
        service2 = AsyncMock(side_effect=Exception("Service 2 failed"))

        result = await call_text_generation_with_fallback(
            prompt="Test prompt",
            task_type="test",
            services=[service1, service2],
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_empty_services_list(self):
        """Test with empty services list."""
        result = await call_text_generation_with_fallback(
            prompt="Test prompt",
            task_type="test",
            services=[],
        )

        assert result is None


class TestTrimText:
    """Tests for trim_text function."""

    def test_trim_short_text(self):
        """Test that short text is not trimmed."""
        result = trim_text("Hello world", limit=50)
        assert result == "Hello world"

    def test_trim_long_text(self):
        """Test that long text is trimmed with ellipsis."""
        long_text = "A" * 200
        result = trim_text(long_text, limit=100)
        assert len(result) == 100
        assert result.endswith("...")

    def test_trim_exact_limit(self):
        """Test text at exact limit is not trimmed."""
        text = "A" * 50
        result = trim_text(text, limit=50)
        assert result == text
        assert "..." not in result

    def test_trim_none_value(self):
        """Test None value returns empty string."""
        result = trim_text(None)
        assert result == ""

    def test_trim_empty_string(self):
        """Test empty string returns empty string."""
        result = trim_text("")
        assert result == ""

    def test_trim_default_limit(self):
        """Test default limit of 160."""
        long_text = "A" * 200
        result = trim_text(long_text)
        assert len(result) == 160


class TestExtractTextContent:
    """Tests for extract_text_content function."""

    def test_extract_from_string(self):
        """Test extracting from string."""
        result = extract_text_content("Hello world")
        assert result == "Hello world"

    def test_extract_from_dict_content(self):
        """Test extracting from dict with 'content' key."""
        result = extract_text_content({"content": "Hello world"})
        assert result == "Hello world"

    def test_extract_from_dict_text(self):
        """Test extracting from dict with 'text' key."""
        result = extract_text_content({"text": "Hello world"})
        assert result == "Hello world"

    def test_extract_from_dict_message(self):
        """Test extracting from dict with 'message' key."""
        result = extract_text_content({"message": "Hello world"})
        assert result == "Hello world"

    def test_extract_from_dict_result(self):
        """Test extracting from dict with 'result' key."""
        result = extract_text_content({"result": "Hello world"})
        assert result == "Hello world"

    def test_extract_from_dict_output(self):
        """Test extracting from dict with 'output' key."""
        result = extract_text_content({"output": "Hello world"})
        assert result == "Hello world"

    def test_extract_from_nested_dict(self):
        """Test extracting from nested dict."""
        result = extract_text_content({"content": {"text": "Hello world"}})
        assert result == "Hello world"

    def test_extract_from_object_with_content(self):
        """Test extracting from object with content attribute."""
        obj = MagicMock()
        obj.content = "Hello world"
        result = extract_text_content(obj)
        assert result == "Hello world"

    def test_extract_from_none(self):
        """Test extracting from None."""
        result = extract_text_content(None)
        assert result is None

    def test_extract_from_empty_dict(self):
        """Test extracting from empty dict."""
        result = extract_text_content({})
        assert result is None

    def test_extract_from_dict_without_text_keys(self):
        """Test extracting from dict without recognized keys."""
        result = extract_text_content({"unknown_key": "value"})
        assert result is None
