"""Logging helpers for AI service manager requests and responses."""

from __future__ import annotations

from typing import Any, Optional

AI_MANAGER_PROVIDER = "ai_service" + "_manager"


def truncate(text: Any, limit: int = 2000) -> str:
    try:
        value = str(text)
    except Exception:
        value = repr(text)
    if not value:
        return ""
    return value if len(value) <= limit else value[:limit] + "...<truncated>"


def log_request(
    logger: Any,
    *,
    task: str,
    provider: Optional[str],
    model: Optional[str],
    params: dict[str, Any] | None = None,
) -> None:
    try:
        logger.info(
            f"LLM Request | task={task} provider={provider or 'auto'} "
            f"model={model or 'auto'} params={params or {}}"
        )
    except Exception:
        pass


def log_prompt(logger: Any, prompt: Optional[str]) -> None:
    if prompt is None:
        return
    try:
        logger.info(f"LLM Prompt Preview: {truncate(prompt, 2000)}")
    except Exception:
        pass


def log_response(
    logger: Any,
    *,
    task: str,
    provider: Optional[str],
    model: Optional[str],
    response: Any,
) -> None:
    try:
        status = "success" if (response and response.success) else "failure"
        if response and not response.success and response.error:
            body_preview = f"ERROR: {truncate(response.error, 2000)}"
        else:
            body_preview = truncate(response.data if response else None, 2000)
        usage = getattr(response, "usage", None)
        provider_name = (
            response.provider if response and response.provider else provider
        )
        model_name = response.model if response and response.model else model
        logger.info(
            f"LLM Response | task={task} provider={provider_name} "
            f"model={model_name} status={status} usage={usage} body={body_preview}"
        )
    except Exception:
        pass
