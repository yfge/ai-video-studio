"""
Tests for retry utilities.
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from app.services.providers.retry_utils import (
    async_retry,
    async_retry_with_auth_refresh,
)


class TestAsyncRetry:
    """Test async_retry decorator."""

    @pytest.mark.asyncio
    async def test_success_no_retry(self):
        """Test successful call without retry."""
        mock_func = AsyncMock(return_value="success")
        decorated = async_retry(max_attempts=3)(mock_func)

        result = await decorated()

        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_transient_http_error(self):
        """Test retry on transient HTTP status codes."""
        mock_func = AsyncMock(
            side_effect=[
                httpx.HTTPStatusError(
                    "Service unavailable",
                    request=Mock(),
                    response=Mock(status_code=503),
                ),
                "success",
            ]
        )
        decorated = async_retry(max_attempts=3, initial_delay=0.01)(mock_func)

        result = await decorated()

        assert result == "success"
        assert mock_func.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_multiple_transient_errors(self):
        """Test multiple retries before success."""
        mock_func = AsyncMock(
            side_effect=[
                httpx.HTTPStatusError(
                    "Rate limited", request=Mock(), response=Mock(status_code=429)
                ),
                httpx.HTTPStatusError(
                    "Server error", request=Mock(), response=Mock(status_code=500)
                ),
                "success",
            ]
        )
        decorated = async_retry(max_attempts=5, initial_delay=0.01)(mock_func)

        result = await decorated()

        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_max_attempts_exceeded(self):
        """Test failure after max attempts exceeded."""
        mock_func = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Service unavailable", request=Mock(), response=Mock(status_code=503)
            )
        )
        decorated = async_retry(max_attempts=2, initial_delay=0.01)(mock_func)

        with pytest.raises(httpx.HTTPStatusError):
            await decorated()

        assert mock_func.call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self):
        """Test no retry on non-transient status codes."""
        mock_func = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not found", request=Mock(), response=Mock(status_code=404)
            )
        )
        decorated = async_retry(max_attempts=3, initial_delay=0.01)(mock_func)

        with pytest.raises(httpx.HTTPStatusError):
            await decorated()

        assert mock_func.call_count == 1  # No retries

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        """Test retry on timeout exceptions."""
        mock_func = AsyncMock(
            side_effect=[httpx.TimeoutException("Timeout"), "success"]
        )
        decorated = async_retry(max_attempts=3, initial_delay=0.01)(mock_func)

        result = await decorated()

        assert result == "success"
        assert mock_func.call_count == 2

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff timing."""
        call_times = []

        async def mock_func():
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 3:
                raise httpx.HTTPStatusError(
                    "Retry", request=Mock(), response=Mock(status_code=503)
                )
            return "success"

        decorated = async_retry(max_attempts=3, initial_delay=0.1, backoff_factor=2)(
            mock_func
        )

        await decorated()

        # Verify delays increase exponentially (with some tolerance)
        assert len(call_times) == 3
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        assert 0.08 < delay1 < 0.15  # ~0.1s ± tolerance
        assert 0.18 < delay2 < 0.25  # ~0.2s ± tolerance

    @pytest.mark.asyncio
    async def test_retry_all_transient_status_codes(self):
        """Test retry on all transient HTTP status codes."""
        transient_codes = [429, 500, 502, 503, 504]

        for status_code in transient_codes:
            mock_func = AsyncMock(
                side_effect=[
                    httpx.HTTPStatusError(
                        "Error", request=Mock(), response=Mock(status_code=status_code)
                    ),
                    "success",
                ]
            )
            decorated = async_retry(max_attempts=3, initial_delay=0.01)(mock_func)

            result = await decorated()

            assert result == "success", f"Failed for status code {status_code}"
            assert mock_func.call_count == 2

    @pytest.mark.asyncio
    async def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        callback_calls = []

        def on_retry_callback(exception, attempt):
            callback_calls.append((exception, attempt))

        mock_func = AsyncMock(
            side_effect=[
                httpx.HTTPStatusError(
                    "Error", request=Mock(), response=Mock(status_code=503)
                ),
                "success",
            ]
        )
        decorated = async_retry(
            max_attempts=3, initial_delay=0.01, on_retry=on_retry_callback
        )(mock_func)

        await decorated()

        assert len(callback_calls) == 1
        assert callback_calls[0][1] == 1  # First retry attempt


class TestAsyncRetryWithAuthRefresh:
    """Test async_retry_with_auth_refresh decorator."""

    @pytest.mark.asyncio
    async def test_success_no_retry(self):
        """Test successful call without retry."""
        mock_func = AsyncMock(return_value="success")
        mock_auth_manager = Mock()
        mock_auth_manager.invalidate_cache = Mock()
        decorated = async_retry_with_auth_refresh(mock_auth_manager, max_attempts=3)(
            mock_func
        )

        result = await decorated()

        assert result == "success"
        assert mock_func.call_count == 1
        mock_auth_manager.invalidate_cache.assert_not_called()

    @pytest.mark.asyncio
    async def test_retry_with_auth_refresh_on_401(self):
        """Test auth refresh on 401 error."""
        mock_func = AsyncMock(
            side_effect=[
                httpx.HTTPStatusError(
                    "Unauthorized", request=Mock(), response=Mock(status_code=401)
                ),
                "success",
            ]
        )
        mock_auth_manager = Mock()
        mock_auth_manager.invalidate_cache = Mock()
        decorated = async_retry_with_auth_refresh(
            mock_auth_manager, max_attempts=3, initial_delay=0.01
        )(mock_func)

        result = await decorated()

        assert result == "success"
        assert mock_func.call_count == 2
        mock_auth_manager.invalidate_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_with_auth_refresh_on_403(self):
        """Test auth refresh on 403 error."""
        mock_func = AsyncMock(
            side_effect=[
                httpx.HTTPStatusError(
                    "Forbidden", request=Mock(), response=Mock(status_code=403)
                ),
                "success",
            ]
        )
        mock_auth_manager = Mock()
        mock_auth_manager.invalidate_cache = Mock()
        decorated = async_retry_with_auth_refresh(
            mock_auth_manager, max_attempts=3, initial_delay=0.01
        )(mock_func)

        result = await decorated()

        assert result == "success"
        assert mock_func.call_count == 2
        mock_auth_manager.invalidate_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_max_attempts_with_auth_refresh(self):
        """Test failure after max auth refresh attempts."""
        mock_func = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Unauthorized", request=Mock(), response=Mock(status_code=401)
            )
        )
        mock_auth_manager = Mock()
        mock_auth_manager.invalidate_cache = Mock()
        decorated = async_retry_with_auth_refresh(
            mock_auth_manager, max_attempts=2, initial_delay=0.01
        )(mock_func)

        with pytest.raises(httpx.HTTPStatusError):
            await decorated()

        assert mock_func.call_count == 2
        # on_retry callback is called only before retries, not on last attempt
        assert mock_auth_manager.invalidate_cache.call_count == 1
