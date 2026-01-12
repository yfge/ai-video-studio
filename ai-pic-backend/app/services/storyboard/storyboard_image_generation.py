from __future__ import annotations

from typing import Any, Sequence

from app.core.config import settings
from app.prompts.template_audit import build_prompt_template_audit, sha256_text
from app.services.image_gen import (
    ImageGenDomain,
    ImageGenMode,
    ImageGenRequest,
    build_ai_manager_call,
    normalize_image_gen_request,
)
from app.services.image_gen.refs import hash_reference_images


def _get_backend_base() -> str:
    return (
        getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
    ).rstrip("/")


def _extract_urls(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return []

    urls: list[str] = []
    url_single = data.get("image_url") or data.get("url")
    if isinstance(url_single, str) and url_single:
        urls.append(url_single)

    images = data.get("images")
    if isinstance(images, list):
        for item in images:
            if isinstance(item, str) and item:
                urls.append(item)
            elif isinstance(item, dict) and item.get("url"):
                urls.append(str(item.get("url")))
    return urls


def _dedupe_urls(urls: Sequence[str]) -> list[str]:
    deduped: list[str] = []
    for url in urls or []:
        if not isinstance(url, str):
            continue
        value = url.strip()
        if not value or value in deduped:
            continue
        deduped.append(value)
    return deduped


async def generate_storyboard_image_urls(
    *,
    prompt: str,
    refs: Sequence[str],
    model: str | None,
    generation_profile: str | None = None,
    count: int | None,
    size: str | None,
    aspect_ratio: str | None,
    width: int | None,
    height: int | None,
    style: str | None,
    style_preset_id: str | None,
    style_spec: Any | None,
    seed: int | None = None,
    steps: int | None = None,
    cfg_scale: float | None = None,
    negative_prompt: str | None = None,
    strength: float | None = None,
    ai_service: Any,
    backend_base: str | None = None,
) -> dict[str, Any]:
    """Generate storyboard images with unified normalization + provider-safe params."""
    backend = (backend_base or _get_backend_base()).rstrip("/") or _get_backend_base()
    cleaned_refs = [r for r in refs or [] if isinstance(r, str) and r.strip()]

    mode = ImageGenMode.IMAGE_TO_IMAGE if cleaned_refs else ImageGenMode.TEXT_TO_IMAGE
    base_image = cleaned_refs[0] if cleaned_refs else None
    extra_images = cleaned_refs[1:] if len(cleaned_refs) > 1 else []

    normalized = normalize_image_gen_request(
        ImageGenRequest(
            domain=ImageGenDomain.STORYBOARD,
            mode=mode,
            prompt=prompt,
            model=model,
            generation_profile=generation_profile,
            style=style,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
            count=count,
            size=size,
            aspect_ratio=aspect_ratio,
            width=width,
            height=height,
            seed=seed,
            steps=steps,
            cfg_scale=cfg_scale,
            negative_prompt=negative_prompt,
            strength=strength,
            base_image=base_image,
            reference_images=extra_images,
            backend_base=backend,
        ),
        strict=False,
    )

    call = build_ai_manager_call(normalized)
    if mode == ImageGenMode.IMAGE_TO_IMAGE:
        if not call.get("image_url"):
            raise RuntimeError("Storyboard img2img missing base image URL")
        response = await ai_service.ai_manager.image_to_image(**call)
    else:
        response = await ai_service.ai_manager.generate_image(**call)

    if not response.success:
        raise RuntimeError(response.error or "Storyboard image generation failed")

    urls = _dedupe_urls(_extract_urls(response.data))
    if not urls:
        raise RuntimeError("Storyboard image generation returned no images")

    response_meta = getattr(response, "metadata", None)
    if not isinstance(response_meta, dict):
        response_meta = {}

    extra = list(normalized.extra_images or [])
    prompt_template = build_prompt_template_audit("storyboard_image_prompt")
    image_gen_meta = {
        "domain": normalized.domain.value,
        "mode": normalized.mode.value,
        "provider": normalized.provider,
        "model_id": normalized.model_id,
        "generation_profile": normalized.generation_profile,
        "size": normalized.size,
        "aspect_ratio": normalized.aspect_ratio,
        "seed": normalized.seed,
        "steps": normalized.steps,
        "cfg_scale": normalized.cfg_scale,
        "negative_prompt": normalized.negative_prompt,
        "strength": normalized.strength,
        "image_reference": normalized.image_reference,
        "image_fidelity": normalized.image_fidelity,
        "human_fidelity": normalized.human_fidelity,
        "prompt_template": prompt_template,
        "prompt_sha256": sha256_text(prompt),
        "reference_images_count": len(extra),
        "reference_images_hash": hash_reference_images(extra),
        "audit_warnings": list(normalized.audit.warnings or []),
    }

    return {
        "urls": urls,
        "provider": response.provider,
        "model": response.model,
        "style_spec": response_meta.get("style_spec"),
        "style_spec_resolution": response_meta.get("style_spec_resolution"),
        "image_gen": image_gen_meta,
    }
