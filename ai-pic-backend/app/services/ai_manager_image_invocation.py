from __future__ import annotations

from typing import Any

from app.services.llm_invocation import (
    LLMInvocationHandle,
    begin_llm_invocation,
    finish_llm_invocation,
)
from app.services.media import invocation_assets
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
    original_prompt: str,
    effective_prompt: str,
    input_references: list[dict[str, Any]],
    request_parameters: dict[str, Any],
) -> LLMInvocationHandle | None:
    return begin_llm_invocation(
        invocation_type=invocation_type,
        call_scene=call_scene,
        provider=provider,
        model=model,
        attempt_index=attempt_index,
        original_prompt=original_prompt,
        prompt=effective_prompt,
        system_prompt=None,
        input_references=input_references,
        request_parameters=safe_media_parameters(request_parameters),
    )


def fail_attempt(handle: LLMInvocationHandle | None, error: str) -> None:
    finish_llm_invocation(handle, error=error)


async def finish_attempt(
    handle: LLMInvocationHandle | None,
    response: Any,
    *,
    provider: str,
    model: str | None,
    prefix: str,
    logger: Any,
) -> None:
    if not response.success:
        finish_llm_invocation(handle, response=response)
        return
    persisted = await invocation_assets.persist_generated_images(
        (response.data or {}).get("images"),
        prefix=prefix,
        provider=provider,
        model=model,
        logger=logger,
    )
    if isinstance(response.data, dict):
        response.data["images"] = persisted.urls
    invocation_assets.attach_invocation_id(response, handle.row_id if handle else None)
    finish_llm_invocation(
        handle,
        response=response,
        status=("succeeded" if persisted.fully_persisted else "output_persist_failed"),
        output_assets=persisted.assets,
        response_data=invocation_assets.image_audit_response(response.data, persisted),
        response_metadata=safe_media_parameters(response.metadata),
    )
