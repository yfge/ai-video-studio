from __future__ import annotations

import inspect
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.repositories.llm_invocation_repository import LLMInvocationRepository
from app.services.llm_invocation_payload import json_safe as _json_safe
from app.services.llm_invocation_payload import (
    normalize_token_usage,
)
from app.services.llm_invocation_payload import serialize_text as _serialize_text

logger = get_logger(__name__)

_INTERNAL_SCENE_MODULES = {
    __name__,
    "app.services.ai.structured_output",
}
_INTERNAL_SCENE_FUNCTIONS = {
    "generate_text",
    "generate_text_with_fallback",
    "generate_image",
    "generate_video",
    "image_to_image",
}
_UNSET = object()


@dataclass(frozen=True)
class LLMInvocationHandle:
    row_id: int
    started_monotonic: float


def infer_call_scene() -> str:
    """Return the first caller outside the shared LLM plumbing."""
    frame = inspect.currentframe()
    try:
        caller = frame.f_back if frame else None
        while caller:
            module = str(caller.f_globals.get("__name__") or "unknown")
            function = caller.f_code.co_name
            shared_llm_frame = (
                module.startswith("app.services.")
                and function in _INTERNAL_SCENE_FUNCTIONS
            )
            if module not in _INTERNAL_SCENE_MODULES and not shared_llm_frame:
                return f"{module}.{caller.f_code.co_name}"
            caller = caller.f_back
    finally:
        del frame
    return "unknown"


def begin_llm_invocation(
    *,
    call_scene: str,
    provider: str,
    model: str | None,
    attempt_index: int,
    prompt: str,
    system_prompt: str | None,
    request_parameters: dict[str, Any],
    invocation_type: str = "text",
    original_prompt: str | None = None,
    input_references: list[dict[str, Any]] | None = None,
) -> LLMInvocationHandle | None:
    session = SessionLocal()
    started = time.perf_counter()
    try:
        row = LLMInvocationRepository(session).create(
            invocation_type=invocation_type,
            call_scene=call_scene,
            provider=provider,
            model=model,
            attempt_index=attempt_index,
            status="processing",
            original_prompt=original_prompt if original_prompt is not None else prompt,
            prompt=prompt,
            system_prompt=system_prompt,
            request_parameters=_json_safe(request_parameters),
            input_references=_json_safe(input_references),
        )
        session.commit()
        session.refresh(row)
        return LLMInvocationHandle(row_id=row.id, started_monotonic=started)
    except Exception:
        session.rollback()
        logger.exception("Failed to persist LLM invocation start")
        return None
    finally:
        session.close()


def finish_llm_invocation(
    handle: LLMInvocationHandle | None,
    *,
    response: Any = None,
    error: str | None = None,
    status: str | None = None,
    output_assets: list[dict[str, Any]] | None = None,
    provider_task_id: str | None = None,
    response_data: Any = _UNSET,
    response_metadata: Any = _UNSET,
    complete: bool = True,
) -> None:
    if handle is None:
        return

    _update_llm_invocation(
        handle.row_id,
        handle=handle,
        response=response,
        error=error,
        status=status,
        output_assets=output_assets,
        provider_task_id=provider_task_id,
        response_data=response_data,
        response_metadata=response_metadata,
        complete=complete,
    )


def complete_llm_invocation(
    invocation_id: int | None,
    *,
    status: str,
    response_data: Any = _UNSET,
    error: str | None = None,
    output_assets: list[dict[str, Any]] | None = None,
) -> None:
    if invocation_id is None:
        return
    _update_llm_invocation(
        invocation_id,
        status=status,
        response_data=response_data,
        error=error,
        output_assets=output_assets,
        complete=True,
    )


def _update_llm_invocation(
    invocation_id: int,
    *,
    handle: LLMInvocationHandle | None = None,
    response: Any = None,
    error: str | None = None,
    status: str | None = None,
    output_assets: list[dict[str, Any]] | None = None,
    provider_task_id: str | None = None,
    response_data: Any = _UNSET,
    response_metadata: Any = _UNSET,
    complete: bool,
) -> None:
    session = SessionLocal()
    try:
        repository = LLMInvocationRepository(session)
        row = repository.get_by_id(invocation_id)
        if row is None:
            return

        usage = getattr(response, "usage", None) if response is not None else None
        metadata = getattr(response, "metadata", None) if response is not None else None
        input_tokens, cache_tokens, output_tokens = normalize_token_usage(
            usage, metadata
        )
        response_error = (
            getattr(response, "error", None) if response is not None else None
        )
        success = bool(getattr(response, "success", False))
        response_provider = getattr(response, "provider", None)
        response_model = getattr(response, "model", None)
        values: dict[str, Any] = {
            "status": status or ("succeeded" if success and not error else "failed"),
            "error": error or response_error,
        }
        if response is not None:
            values.update(
                provider=response_provider or row.provider,
                model=response_model or row.model,
                usage=_json_safe(usage),
                response_metadata=_json_safe(
                    metadata if response_metadata is _UNSET else response_metadata
                ),
                input_tokens=input_tokens,
                cache_tokens=cache_tokens,
                output_tokens=output_tokens,
            )
        if output_assets is not None:
            values["output_assets"] = _json_safe(output_assets)
        if provider_task_id is not None:
            values["provider_task_id"] = provider_task_id
        if response is not None or response_data is not _UNSET:
            payload = (
                getattr(response, "data", None)
                if response_data is _UNSET
                else response_data
            )
            values["response"] = _serialize_text(payload)
        if complete:
            now = datetime.now(timezone.utc)
            values["finished_at"] = now
            values["latency_ms"] = _elapsed_ms(row.started_at, now, handle)
        repository.update(row, **values)
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Failed to persist LLM invocation result")
    finally:
        session.close()


def _elapsed_ms(
    started_at: datetime | None,
    now: datetime,
    handle: LLMInvocationHandle | None,
) -> int | None:
    if handle is not None:
        return max(0, int((time.perf_counter() - handle.started_monotonic) * 1000))
    if started_at is None:
        return None
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    return max(0, int((now - started_at).total_seconds() * 1000))
