"""
Retry Utilities with Exponential Backoff

Provides async retry decorators for handling transient errors in API calls.
"""

import asyncio
import functools
from typing import Any, Callable, Optional, Tuple, Type, TypeVar

import httpx
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


# Default retryable HTTP status codes (rate limits, server errors, timeouts)
DEFAULT_RETRYABLE_STATUS_CODES = {
    429,  # Too Many Requests
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
}

# Default retryable error codes from providers
DEFAULT_RETRYABLE_ERROR_CODES = {
    1002,  # Rate limit (Keling/MiniMax)
    1039,  # TPM rate limit (MiniMax)
    5000,  # Server error (Keling)
    5001,  # Service unavailable (Keling)
    5002,  # Timeout (Keling)
}


def async_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        httpx.HTTPStatusError,
        httpx.TimeoutException,
        httpx.NetworkError,
        ConnectionError,
    ),
    retryable_status_codes: Optional[set] = None,
    retryable_error_codes: Optional[set] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    Async retry decorator with exponential backoff.

    Automatically retries async functions that raise retryable exceptions,
    with configurable backoff strategy.

    Args:
        max_attempts: Maximum number of attempts (including initial)
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries (caps exponential growth)
        backoff_factor: Multiplier for exponential backoff (2.0 = double each time)
        retryable_exceptions: Tuple of exception types to retry
        retryable_status_codes: HTTP status codes that should trigger retry
        retryable_error_codes: Provider error codes that should trigger retry
        on_retry: Optional callback function(exception, attempt_number)

    Example:
        @async_retry(max_attempts=5, initial_delay=2.0, backoff_factor=2.0)
        async def call_api():
            response = await client.post("/endpoint", json=data)
            return response.json()

    Returns:
        Decorated async function that will retry on transient errors
    """
    if retryable_status_codes is None:
        retryable_status_codes = DEFAULT_RETRYABLE_STATUS_CODES
    if retryable_error_codes is None:
        retryable_error_codes = DEFAULT_RETRYABLE_ERROR_CODES

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            delay = initial_delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except retryable_exceptions as e:
                    last_exception = e

                    # Check if this specific error should be retried
                    should_retry = False

                    # Check HTTP status code
                    if isinstance(e, httpx.HTTPStatusError):
                        if e.response.status_code in retryable_status_codes:
                            should_retry = True
                            logger.warning(
                                f"{func.__name__} failed with HTTP {e.response.status_code} "
                                f"(attempt {attempt}/{max_attempts})"
                            )

                    # Check provider error code
                    elif (
                        hasattr(e, "status_code")
                        and e.status_code in retryable_error_codes
                    ):
                        should_retry = True
                        logger.warning(
                            f"{func.__name__} failed with error code {e.status_code} "
                            f"(attempt {attempt}/{max_attempts}): {e}"
                        )

                    # Other retryable exceptions (timeout, network errors)
                    elif isinstance(
                        e, (httpx.TimeoutException, httpx.NetworkError, ConnectionError)
                    ):
                        should_retry = True
                        logger.warning(
                            f"{func.__name__} failed with {type(e).__name__} "
                            f"(attempt {attempt}/{max_attempts}): {e}"
                        )

                    # If not retryable or last attempt, raise immediately
                    if not should_retry or attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed permanently after {attempt} attempts"
                        )
                        raise

                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(e, attempt)
                        except Exception as callback_error:
                            logger.error(
                                f"Retry callback failed: {callback_error}",
                                exc_info=True,
                            )

                    # Wait before next retry
                    if attempt < max_attempts:
                        logger.info(f"Retrying {func.__name__} in {delay:.1f}s...")
                        await asyncio.sleep(delay)

                        # Calculate next delay with exponential backoff
                        delay = min(delay * backoff_factor, max_delay)

            # Should not reach here, but handle just in case
            if last_exception:
                raise last_exception
            else:
                raise RuntimeError(
                    f"{func.__name__} failed after {max_attempts} attempts"
                )

        return wrapper

    return decorator


def async_retry_with_auth_refresh(auth_manager, max_attempts: int = 3, **retry_kwargs):
    """
    Specialized retry decorator that handles authentication token expiry.

    Automatically refreshes authentication tokens on 401/403/1004 errors
    before retrying the request.

    Args:
        auth_manager: Authentication manager with invalidate_cache() method
        max_attempts: Maximum retry attempts
        **retry_kwargs: Additional arguments passed to async_retry

    Example:
        @async_retry_with_auth_refresh(auth_manager, max_attempts=5)
        async def call_authenticated_api():
            headers = auth_manager.get_auth_header()
            response = await client.post("/endpoint", headers=headers)
            return response.json()
    """
    auth_error_codes = {401, 403, 1004}  # HTTP + Keling auth error code

    def on_auth_retry(exception: Exception, attempt: int):
        """Callback to refresh auth token on auth errors."""
        is_auth_error = False

        if isinstance(exception, httpx.HTTPStatusError):
            if exception.response.status_code in auth_error_codes:
                is_auth_error = True

        elif hasattr(exception, "status_code") and exception.status_code == 1004:
            is_auth_error = True

        if is_auth_error:
            logger.info(
                f"Authentication error detected (attempt {attempt}), "
                f"invalidating token cache and refreshing"
            )
            auth_manager.invalidate_cache()

    # Add auth error codes to retryable status codes
    retryable_status_codes = (
        retry_kwargs.get("retryable_status_codes", set()) | auth_error_codes
    )
    retry_kwargs["retryable_status_codes"] = retryable_status_codes

    # Add auth error code 1004 to retryable error codes
    retryable_error_codes = retry_kwargs.get("retryable_error_codes", set()) | {1004}
    retry_kwargs["retryable_error_codes"] = retryable_error_codes

    # Set on_retry callback
    retry_kwargs["on_retry"] = on_auth_retry

    return async_retry(max_attempts=max_attempts, **retry_kwargs)
