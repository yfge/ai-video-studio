"""Prompt/runtime helpers for storyboard image task generation."""

from __future__ import annotations

from typing import Any

from app.prompts.templates import PromptTemplate
from app.services.image_gen import ImageGenMode
from app.services.image_gen.provider_params import supported_ai_manager_keys
from app.services.storyboard.storyboard_prompt_compiler import StoryboardPromptCompiler
from app.utils.model_utils import infer_provider_from_model, parse_model_and_provider

from .utils import build_reference_image_context


def resolve_dimensions(width, height, size):
    w, h = width, height
    if (w is None or h is None) and isinstance(size, str) and size.strip():
        from app.services.providers.image_param_utils import size_to_dimensions

        dims = size_to_dimensions(size)
        if dims:
            w, h = dims
    return w or 1024, h or 1024


def frame_base_prompt(
    frame: dict[str, Any],
    frame_index: int,
    *,
    prompt_override: str | None,
    prompt_manager,
) -> tuple[str, str]:
    base_prompt = frame.get("ai_prompt") or frame.get("description") or ""
    override_clean = (prompt_override or "").strip()
    if override_clean:
        base_prompt = override_clean
    if not base_prompt:
        base_prompt = prompt_manager.render_prompt(
            PromptTemplate.STORYBOARD_IMAGE_FALLBACK.value,
            {
                "frame_index": frame_index + 1,
                "scene_number": frame.get("scene_number"),
            },
        )
    return base_prompt, override_clean


def compile_storyboard_image_prompt(
    frame: dict[str, Any],
    *,
    base_prompt: str,
    reference_notes: list[dict[str, Any]],
    model: str | None,
) -> dict[str, Any]:
    provider = _resolve_provider(model)
    return StoryboardPromptCompiler().compile_frame(
        frame,
        base_prompt=base_prompt,
        reference_notes=reference_notes,
        provider=provider,
        negative_prompt_supported=_negative_prompt_supported(provider),
    )


def render_storyboard_image_prompt(
    compiled_prompt: dict[str, Any],
    *,
    reference_notes: list[dict[str, Any]],
    labeled_references: list[dict[str, Any]] | None,
    prompt_manager,
) -> str:
    prompt = prompt_manager.render_prompt(
        PromptTemplate.STORYBOARD_IMAGE_PROMPT.value,
        {
            "base_prompt": compiled_prompt["image_prompt"],
            "reference_notes": reference_notes,
        },
    )
    if labeled_references:
        ref_context = build_reference_image_context(labeled_references)
        if ref_context:
            prompt = ref_context + chr(10) + chr(10) + prompt
    return prompt


def _resolve_provider(model: str | None) -> str | None:
    clean_model, provider_hint = parse_model_and_provider(model)
    provider = provider_hint or (
        infer_provider_from_model(clean_model or "") if clean_model else None
    )
    return provider.lower() if provider else None


def _negative_prompt_supported(provider: str | None) -> bool:
    if not provider:
        return True
    try:
        return "negative_prompt" in supported_ai_manager_keys(
            provider,
            ImageGenMode.TEXT_TO_IMAGE,
        )
    except Exception:
        return True
