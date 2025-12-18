"""
Text generation utilities.

Provides helper functions for text generation services.
"""

from typing import Any, Callable, List, Optional

from app.core.logging import get_logger


logger = get_logger()


async def call_text_generation_with_fallback(
    prompt: str,
    task_type: str,
    services: List[Callable],
) -> Optional[str]:
    """
    Call text generation services with fallback support.

    Args:
        prompt: Text generation prompt.
        task_type: Type of task (for logging).
        services: List of service functions to try in order.

    Returns:
        Generated text or None if all services fail.
    """
    for service in services:
        try:
            result = await service(prompt, task_type)
            if result:
                return result
        except Exception as e:
            logger.warning(f"Service {service.__name__} failed: {e}")
            continue

    return None


def trim_text(value: Optional[str], limit: int = 160) -> str:
    """
    Trim text to a maximum length, adding ellipsis if truncated.

    Args:
        value: Text to trim.
        limit: Maximum length.

    Returns:
        Trimmed text with ellipsis if truncated.
    """
    if not value:
        return ""
    if len(value) <= limit:
        return value
    return value[:limit - 3] + "..."


def extract_text_content(response: Any) -> Optional[str]:
    """
    Extract text content from various AI response formats.

    Args:
        response: AI response object or dictionary.

    Returns:
        Extracted text content or None.
    """
    if response is None:
        return None

    # Handle string response
    if isinstance(response, str):
        return response

    # Handle dictionary response
    if isinstance(response, dict):
        # Common response keys
        for key in ["content", "text", "message", "result", "output"]:
            if key in response:
                value = response[key]
                if isinstance(value, str):
                    return value
                elif isinstance(value, dict):
                    return extract_text_content(value)

    # Handle object with content attribute
    if hasattr(response, "content"):
        return extract_text_content(response.content)

    return None
