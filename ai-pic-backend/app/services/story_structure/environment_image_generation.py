from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.config import settings
from app.models.story_structure import Environment
from app.prompts.template_audit import build_prompt_template_audit, sha256_text
from app.services.image_gen import (
    ImageGenDomain,
    ImageGenMode,
    ImageGenRequest,
    build_ai_manager_call,
    normalize_image_gen_request,
)
from app.services.image_gen.coerce import clean_str
from sqlalchemy.orm import Session

from .environment_image_prompts import (
    DEFAULT_ENV_VARIANT_EXTRA_PROMPT,
    compose_environment_prompt,
)
from .environment_image_requests import (
    EnvironmentImageVariantRequest,
    EnvironmentTextToImageRequest,
)
from .environment_image_storage import persist_environment_images


def _get_backend_base() -> str:
    return (
        getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
    ).rstrip("/")


async def generate_environment_images(
    *,
    db: Session,
    env: Environment,
    request: EnvironmentTextToImageRequest,
    ai_service: Any,
    require_upload: bool,
) -> list[str]:
    final_prompt = compose_environment_prompt(env, request.prompt)
    prompt_template = build_prompt_template_audit("environment_image")
    prompt_sha256 = sha256_text(final_prompt)

    normalized = normalize_image_gen_request(
        ImageGenRequest(
            domain=ImageGenDomain.ENVIRONMENT,
            mode=ImageGenMode.TEXT_TO_IMAGE,
            prompt=final_prompt,
            model=request.model,
            generation_profile=request.generation_profile,
            style=request.style,
            style_preset_id=request.style_preset_id,
            style_spec=request.style_spec,
            count=request.count,
            size=request.size,
            aspect_ratio=request.aspect_ratio,
            seed=request.seed,
            steps=request.steps,
            cfg_scale=request.cfg_scale,
            negative_prompt=request.negative_prompt,
        ),
        strict=False,
    )

    call = build_ai_manager_call(normalized)
    response = await ai_service.ai_manager.generate_image(**call)
    if not response.success:
        raise RuntimeError(response.error or "环境文生图生成失败")
    images = response.data.get("images", []) if isinstance(response.data, dict) else []
    if not images:
        raise RuntimeError("环境文生图接口未返回任何图像")

    saved_urls = await persist_environment_images(
        db=db,
        env=env,
        image_urls=images,
        ai_service=ai_service,
        require_upload=require_upload,
    )

    response_meta = getattr(response, "metadata", None)
    if not isinstance(response_meta, dict):
        response_meta = {}

    extra = dict(env.extra_metadata or {})
    extra["last_text_to_image_generation"] = {
        "generated_at": datetime.utcnow().isoformat(),
        "prompt_template": prompt_template,
        "prompt_sha256": prompt_sha256,
        "style": normalized.style,
        "style_preset_id": normalized.style_preset_id,
        "style_spec": response_meta.get("style_spec"),
        "style_spec_resolution": response_meta.get("style_spec_resolution"),
        "provider": response.provider,
        "model": response.model,
        "generation_profile": normalized.generation_profile,
        "seed": normalized.seed,
        "steps": normalized.steps,
        "cfg_scale": normalized.cfg_scale,
        "negative_prompt": normalized.negative_prompt,
        "count": len(saved_urls),
        "audit_warnings": list(normalized.audit.warnings or []),
    }
    env.extra_metadata = extra
    db.commit()
    db.refresh(env)

    return saved_urls


async def generate_environment_image_variants(
    *,
    db: Session,
    env: Environment,
    request: EnvironmentImageVariantRequest,
    ai_service: Any,
    require_upload: bool,
    backend_base: str | None = None,
) -> list[str]:
    base_image_input = clean_str(request.base_image)
    if not base_image_input:
        raise RuntimeError("缺少基准图像")

    prompt_hint = request.prompt or DEFAULT_ENV_VARIANT_EXTRA_PROMPT
    final_prompt = compose_environment_prompt(env, prompt_hint)
    prompt_template = build_prompt_template_audit("environment_image")
    prompt_sha256 = sha256_text(final_prompt)

    normalized = normalize_image_gen_request(
        ImageGenRequest(
            domain=ImageGenDomain.ENVIRONMENT,
            mode=ImageGenMode.IMAGE_TO_IMAGE,
            prompt=final_prompt,
            model=request.model,
            generation_profile=request.generation_profile,
            style=request.style,
            style_preset_id=request.style_preset_id,
            style_spec=request.style_spec,
            count=request.count,
            size=request.size,
            aspect_ratio=request.aspect_ratio,
            seed=request.seed,
            steps=request.steps,
            cfg_scale=request.cfg_scale,
            negative_prompt=request.negative_prompt,
            strength=request.strength,
            base_image=base_image_input,
            reference_images=request.reference_images,
            backend_base=(backend_base or _get_backend_base()),
        ),
        strict=False,
    )

    call = build_ai_manager_call(normalized)
    if not call.get("image_url"):
        raise RuntimeError("基准图 URL 缺失，无法执行环境图生图")

    response = await ai_service.ai_manager.image_to_image(**call)
    if not response.success:
        raise RuntimeError(response.error or "环境图生图生成失败")
    images = response.data.get("images", []) if isinstance(response.data, dict) else []
    if not images:
        raise RuntimeError("环境图生图接口未返回任何图像")

    saved_urls = await persist_environment_images(
        db=db,
        env=env,
        image_urls=images,
        ai_service=ai_service,
        require_upload=require_upload,
    )

    response_meta = getattr(response, "metadata", None)
    if not isinstance(response_meta, dict):
        response_meta = {}

    extra = dict(env.extra_metadata or {})
    extra["last_image_to_image_generation"] = {
        "generated_at": datetime.utcnow().isoformat(),
        "prompt_template": prompt_template,
        "prompt_sha256": prompt_sha256,
        "style": normalized.style,
        "style_preset_id": normalized.style_preset_id,
        "style_spec": response_meta.get("style_spec"),
        "style_spec_resolution": response_meta.get("style_spec_resolution"),
        "provider": response.provider,
        "model": response.model,
        "generation_profile": normalized.generation_profile,
        "seed": normalized.seed,
        "steps": normalized.steps,
        "cfg_scale": normalized.cfg_scale,
        "negative_prompt": normalized.negative_prompt,
        "strength": normalized.strength,
        "count": len(saved_urls),
        "audit_warnings": list(normalized.audit.warnings or []),
    }
    env.extra_metadata = extra
    db.commit()
    db.refresh(env)

    return saved_urls
