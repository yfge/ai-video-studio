"""Failure response helpers for AI manager fallback paths."""

from __future__ import annotations

from typing import Optional

from app.services.ai_manager_logging import AI_MANAGER_PROVIDER

from .providers.base import AIModelType, AIResponse, AITaskType


def failure_response(
    *,
    error: str,
    provider: str,
    model: Optional[str],
    task_type: AITaskType,
    model_type: AIModelType,
) -> AIResponse:
    return AIResponse(
        success=False,
        error=error,
        provider=provider,
        model=model or "unknown",
        task_type=task_type,
        model_type=model_type,
    )


def manager_failure_response(
    *,
    error: str,
    model: Optional[str],
    task_type: AITaskType,
    model_type: AIModelType,
) -> AIResponse:
    return failure_response(
        error=error,
        provider=AI_MANAGER_PROVIDER,
        model=model,
        task_type=task_type,
        model_type=model_type,
    )


def exception_failure_response(
    *,
    action: str,
    exc: Exception,
    provider: str,
    model: Optional[str],
    task_type: AITaskType,
    model_type: AIModelType,
) -> AIResponse:
    return failure_response(
        error=f"{action}: {str(exc)}",
        provider=provider,
        model=model,
        task_type=task_type,
        model_type=model_type,
    )


def provider_prefixed_error(
    error: Optional[str],
    provider: Optional[str],
    *,
    default_error: str = "未知错误",
) -> str:
    error_msg = (error or "").strip() or default_error
    if provider and not error_msg.lower().startswith(provider.lower()):
        return f"{provider}: {error_msg}"
    return error_msg


def terminal_failure_response(
    *,
    default_error: str,
    last_error: Optional[str],
    last_provider: Optional[str],
    model: Optional[str],
    task_type: AITaskType,
    model_type: AIModelType,
    default_unknown_error: str = "未知错误",
) -> AIResponse:
    provider = last_provider or AI_MANAGER_PROVIDER
    error = (
        provider_prefixed_error(
            last_error,
            last_provider,
            default_error=default_unknown_error,
        )
        if last_error is not None
        else default_error
    )
    return failure_response(
        error=error,
        provider=provider,
        model=model,
        task_type=task_type,
        model_type=model_type,
    )
