"""Image generation via the ChatGPT Codex responses endpoint.

Uses the Responses API `image_generation` tool with the Codex OAuth token, so
image output is billed to the ChatGPT subscription instead of an API key.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from .codex_image_aspect import (
    image_matches_aspect_ratio,
    prompt_with_aspect_contract,
    resolve_image_size,
)
from .codex_image_payload import build_codex_image_payload, parse_codex_image_sse
from .codex_image_references import clean_reference_images, inline_reference_images

DEFAULT_IMAGE_TOOL_MODEL = "gpt-5.4"


def _generation_payload(prompt, aspect_ratio, size, references):
    return build_codex_image_payload(
        prompt=prompt_with_aspect_contract(prompt, aspect_ratio),
        model=DEFAULT_IMAGE_TOOL_MODEL,
        size=size,
        reference_images=references,
    )


async def _uploaded_reference_payload(
    *, prompt, aspect_ratio, size, cleaned, upload_references, logger
):
    file_ids = await upload_references(cleaned)
    if len(file_ids) != len(cleaned):
        raise RuntimeError("Codex reference upload returned incomplete file IDs")
    prepared = [{"file_id": file_id} for file_id in file_ids]
    logger.info(
        "Codex reference files uploaded after URL timeout | refs=%s", len(prepared)
    )
    return _generation_payload(prompt, aspect_ratio, size, prepared), prepared


def _candidate_matches(candidate, meta, aspect_ratio):
    if not candidate:
        return False, meta
    matches, dimensions = image_matches_aspect_ratio(candidate, aspect_ratio)
    if dimensions:
        meta["actual_width"], meta["actual_height"] = dimensions
    if not matches:
        meta["error"] = (
            "Codex image physical aspect ratio mismatch: "
            f"expected={aspect_ratio}, actual={dimensions}"
        )
    return matches, meta


async def _recover_reference_timeout(
    *,
    exc,
    payload,
    prepared,
    cleaned,
    prompt,
    aspect_ratio,
    size,
    upload_references,
    sleep,
    logger,
):
    if upload_references and cleaned:
        try:
            return await _uploaded_reference_payload(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                size=size,
                cleaned=cleaned,
                upload_references=upload_references,
                logger=logger,
            )
        except Exception as upload_exc:  # noqa: BLE001
            logger.warning(
                "Codex reference file upload fallback failed: %s", upload_exc
            )
            raise exc from upload_exc
    logger.warning("Codex reference download timed out; retrying once: %s", exc)
    await sleep(10)
    return payload, prepared


async def _run_generation_attempts(
    *,
    payload,
    prepared,
    cleaned,
    prompt,
    aspect_ratio,
    size,
    post_raw,
    upload_references,
    sleep,
    logger,
):
    meta: Dict[str, Any] = {}
    for attempt in range(2):
        try:
            raw = await post_raw(payload)
        except Exception as exc:
            if attempt != 0 or not _is_transient_reference_fetch_error(exc):
                raise
            meta = {"error": str(exc)}
            payload, prepared = await _recover_reference_timeout(
                exc=exc,
                payload=payload,
                prepared=prepared,
                cleaned=cleaned,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                size=size,
                upload_references=upload_references,
                sleep=sleep,
                logger=logger,
            )
            continue
        candidate, meta = parse_codex_image_sse(raw)
        matches, meta = _candidate_matches(candidate, meta, aspect_ratio)
        if matches:
            return candidate, meta, prepared
        logger.warning(
            "Codex image_generation failed (attempt %s): %s",
            attempt + 1,
            meta.get("error"),
        )
        if attempt == 0:
            await sleep(10)
    raise RuntimeError(
        meta.get("error") or "Codex image_generation returned no image result"
    )


async def run_codex_image_generation(
    *,
    prompt: str,
    references: Sequence[str] | None,
    size_hint: Optional[str],
    width: Optional[int],
    height: Optional[int],
    aspect_ratio: Optional[str],
    post_raw,
    upload_references=None,
    sleep,
    logger,
) -> tuple[str, Dict[str, Any], str, int]:
    """Run the image tool call with inlined references and one delayed retry.

    Returns (image_data_url, meta, size, reference_count); raises on failure.
    """
    if isinstance(references, str):
        references = [references]
    cleaned = clean_reference_images(references)
    prepared: list[str | Dict[str, str]] = await inline_reference_images(cleaned)
    size = resolve_image_size(size_hint, width, height, aspect_ratio)
    logger.info(
        "Codex image canvas resolved | aspect_ratio=%s size=%s width=%s height=%s refs=%s",
        aspect_ratio,
        size,
        width,
        height,
        len(prepared),
    )
    image_data, meta, prepared = await _run_generation_attempts(
        payload=_generation_payload(prompt, aspect_ratio, size, prepared),
        prepared=prepared,
        cleaned=cleaned,
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        size=size,
        post_raw=post_raw,
        upload_references=upload_references,
        sleep=sleep,
        logger=logger,
    )
    return image_data, meta, size, len(prepared)


def _is_transient_reference_fetch_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "unable to download content" in message and "provided url" in message
