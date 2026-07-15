"""Orchestrate dynamic prompt generation inside storyboard image tasks."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import anyio
from app.core.config import settings
from app.core.logging import get_logger
from app.prompts.template_audit import sha256_text
from app.services.storyboard.dynamic_prompt.cache import (
    compute_input_fingerprint,
    read_cached_bundle,
    write_bundle,
)
from app.services.storyboard.dynamic_prompt.context_builder import (
    build_frame_input,
    build_scene_context,
    group_target_frames_by_scene,
)
from app.services.storyboard.dynamic_prompt.generator import generate_prompts_for_scene

logger = get_logger("storyboard_dynamic_prompt")

PROMPT_SOURCE_DYNAMIC = "llm_dynamic"
FALLBACK_WARNING = "dynamic_prompt_fallback"


def build_dynamic_prompt_bundles(
    script: Any,
    frames: List[dict],
    target_indexes: List[int],
    ref_ctx: Any,
    *,
    style: Optional[str] = None,
    style_spec: Optional[dict] = None,
    prompt_override: Optional[str] = None,
    ai_service: Any = None,
) -> Dict[int, Dict[str, Any]]:
    """Return frame_index -> prompt bundle for the targeted frames.

    Any failure degrades to a partial or empty mapping; missing frames keep
    the compiler-built prompts. Generated bundles are written back onto the
    frame dicts so they persist with the storyboard and act as a cache.
    """
    if not settings.STORYBOARD_DYNAMIC_PROMPT_ENABLED:
        return {}
    if prompt_override and str(prompt_override).strip():
        return {}
    ai_manager = getattr(ai_service, "ai_manager", None)
    if ai_manager is None:
        logger.info("dynamic prompt skipped: ai_manager unavailable")
        return {}

    try:
        return _build_bundles(
            script, frames, target_indexes, ref_ctx, style, style_spec, ai_manager
        )
    except Exception as exc:
        logger.warning(
            "dynamic prompt generation failed, fallback to compiler: %s", exc
        )
        return {}


def _build_bundles(
    script: Any,
    frames: List[dict],
    target_indexes: List[int],
    ref_ctx: Any,
    style: Optional[str],
    style_spec: Optional[dict],
    ai_manager: Any,
) -> Dict[int, Dict[str, Any]]:
    style_summary = _style_summary(style, style_spec)
    groups = group_target_frames_by_scene(frames, target_indexes)
    results: Dict[int, Dict[str, Any]] = {}
    pending: List[tuple[Dict[str, Any], List[Dict[str, Any]], Dict[int, str]]] = []

    for scene_number, indexes in groups.items():
        descriptions = [
            str(frames[i].get("description") or frames[i].get("ai_prompt") or "")
            for i in indexes
        ]
        scene_context = build_scene_context(
            script, scene_number, ref_ctx, descriptions, style=style_summary
        )
        chunk_inputs: List[Dict[str, Any]] = []
        chunk_fingerprints: Dict[int, str] = {}
        for idx in indexes:
            frame_input = build_frame_input(
                frames,
                idx,
                scene_characters=scene_context.get("characters") or [],
                ref_ctx=ref_ctx,
            )
            fingerprint = compute_input_fingerprint(scene_context, frame_input)
            cached = read_cached_bundle(frames[idx], fingerprint)
            if cached:
                results[idx] = cached
                continue
            chunk_inputs.append(frame_input)
            chunk_fingerprints[idx] = fingerprint
        max_per_call = max(1, settings.STORYBOARD_DYNAMIC_PROMPT_MAX_FRAMES_PER_CALL)
        for start in range(0, len(chunk_inputs), max_per_call):
            chunk = chunk_inputs[start : start + max_per_call]
            pending.append((scene_context, chunk, chunk_fingerprints))

    if pending:
        generated = anyio.run(_generate_all, pending, ai_manager)
        for idx, prompts in generated.items():
            fingerprint = _fingerprint_for(pending, idx)
            bundle = {
                "input_sha": fingerprint,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "version": 1,
                **prompts,
            }
            write_bundle(frames[idx], bundle)
            results[idx] = bundle

    logger.info(
        "dynamic prompt bundles ready: %s/%s frames (cache+llm)",
        len(results),
        len(target_indexes),
    )
    return results


async def _generate_all(
    pending: List[tuple[Dict[str, Any], List[Dict[str, Any]], Dict[int, str]]],
    ai_manager: Any,
) -> Dict[int, Dict[str, str]]:
    generated: Dict[int, Dict[str, str]] = {}
    for scene_context, chunk, _fingerprints in pending:
        prompts = await generate_prompts_for_scene(
            scene_context,
            chunk,
            ai_manager=ai_manager,
            model=settings.STORYBOARD_DYNAMIC_PROMPT_MODEL,
        )
        generated.update(prompts)
    return generated


def _fingerprint_for(
    pending: List[tuple[Dict[str, Any], List[Dict[str, Any]], Dict[int, str]]],
    frame_index: int,
) -> str:
    for _context, _chunk, fingerprints in pending:
        if frame_index in fingerprints:
            return fingerprints[frame_index]
    return ""


def apply_dynamic_prompt_bundle(
    compiled_prompt: Dict[str, Any],
    bundle: Optional[Dict[str, Any]],
    *,
    image_limit: int = 2200,
    keyframe_limit: int = 1800,
) -> Dict[str, Any]:
    """Overwrite the compiled prompt fields with the LLM bundle in place.

    With no bundle the compiled dict is returned untouched (plus a fallback
    warning when the feature is enabled), so compiler output stays in effect.
    """
    if not bundle:
        if settings.STORYBOARD_DYNAMIC_PROMPT_ENABLED:
            compiled_prompt.setdefault("warnings", []).append(FALLBACK_WARNING)
        return compiled_prompt
    warnings = compiled_prompt.setdefault("warnings", [])

    compiled_prompt["image_prompt"] = _truncate(
        bundle["image_prompt"], image_limit, "image_prompt_truncated", warnings
    )
    compiled_prompt["start_keyframe_prompt"] = _truncate(
        bundle["start_keyframe_prompt"],
        keyframe_limit,
        "start_keyframe_prompt_truncated",
        warnings,
    )
    compiled_prompt["end_keyframe_prompt"] = _truncate(
        bundle["end_keyframe_prompt"],
        keyframe_limit,
        "end_keyframe_prompt_truncated",
        warnings,
    )
    compiled_prompt["prompt_source"] = PROMPT_SOURCE_DYNAMIC
    compiled_prompt["prompt_sha256"] = sha256_text(compiled_prompt["image_prompt"])
    return compiled_prompt


def _style_summary(style: Optional[str], style_spec: Optional[dict]) -> str:
    bits: List[str] = []
    if style and str(style).strip():
        bits.append(str(style).strip())
    if isinstance(style_spec, dict):
        for key in ("style_name", "name", "aesthetic", "tone"):
            value = style_spec.get(key)
            if isinstance(value, str) and value.strip():
                bits.append(value.strip())
                break
    return "，".join(bits)


def _truncate(text: str, limit: int, warning: str, warnings: List[str]) -> str:
    if len(text) <= limit:
        return text
    warnings.append(warning)
    return text[: limit - 3].rstrip() + "..."
