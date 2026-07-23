from __future__ import annotations

from typing import Any

from app.services.llm_invocation import (
    LLMInvocationHandle,
    begin_llm_invocation,
    complete_llm_invocation,
    finish_llm_invocation,
)
from app.services.media.invocation_assets import (
    attach_invocation_id,
    invocation_id_from_response,
)
from app.services.media.invocation_references import (
    persist_reference_assets,
    safe_media_parameters,
)


async def persist_inputs(
    references: list[tuple[str, str]],
    *,
    provider: str,
    model: str | None,
    logger: Any,
) -> list[dict[str, Any]]:
    return await persist_reference_assets(
        references,
        provider=provider,
        model=model,
        logger=logger,
    )


def begin_attempt(
    *,
    invocation_type: str,
    call_scene: str,
    provider: str,
    model: str | None,
    attempt_index: int,
    prompt: str | None,
    input_references: list[dict[str, Any]],
    request_parameters: dict[str, Any],
) -> LLMInvocationHandle | None:
    return begin_llm_invocation(
        invocation_type=invocation_type,
        call_scene=call_scene,
        provider=provider,
        model=model,
        attempt_index=attempt_index,
        original_prompt=prompt or "",
        prompt=prompt or "",
        system_prompt=None,
        input_references=input_references,
        request_parameters=safe_media_parameters(request_parameters),
    )


def finish_attempt(handle: LLMInvocationHandle | None, response: Any) -> None:
    if not response.success:
        finish_llm_invocation(handle, response=response)
        return
    task_id = (response.data or {}).get("task_id")
    attach_invocation_id(response, handle.row_id if handle else None)
    finish_llm_invocation(
        handle,
        response=response,
        status="submitted" if task_id else "processing",
        provider_task_id=str(task_id) if task_id else None,
        response_data=safe_media_parameters(response.data),
        response_metadata=safe_media_parameters(response.metadata),
        complete=False,
    )


def fail_attempt(handle: LLMInvocationHandle | None, error: str) -> None:
    finish_llm_invocation(handle, error=error)


def fail_submitted_response(response: Any, error: str) -> None:
    complete_llm_invocation(
        invocation_id_from_response(response),
        status="failed",
        error=error,
    )
