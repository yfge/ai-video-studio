from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.schemas.virtual_ip import VirtualIPImageCreate
from app.services.image_gen import (
    ImageGenDomain,
    ImageGenMode,
    ImageGenRequest,
    build_ai_manager_call,
    normalize_image_gen_request,
)
from app.services.image_gen.coerce import (
    clean_str,
    coerce_str_list,
    maybe_int,
    value_from_payload,
)
from app.services.image_gen.refs import hash_reference_images
from app.services.virtual_ip.virtual_ip_image_prompts import (
    render_virtual_ip_image_variant_prompt,
)
from sqlalchemy.orm import Session

DEFAULT_VARIANT_PROMPT = "为当前角色生成不同视角/姿态的图像，如背面照或全身照"


@dataclass(frozen=True, slots=True)
class VirtualIPVariantRequest:
    prompt: str
    model: str | None
    count: int | None
    size: str | None
    aspect_ratio: str | None
    style: str | None
    style_preset_id: str | None
    style_spec: Any | None
    reference_images: list[str]


def resolve_virtual_ip_variant_request(
    payload: Mapping[str, Any],
    *,
    prompt: str | None,
    model: str | None,
    model_id: str | None,
    count: int | None,
    size: str | None,
    aspect_ratio: str | None,
    base_image_model: str | None,
) -> VirtualIPVariantRequest:
    prompt_value = clean_str(value_from_payload(payload, "prompt", prompt))
    if not prompt_value:
        prompt_value = DEFAULT_VARIANT_PROMPT

    raw_model = clean_str(value_from_payload(payload, "model", model))
    selected_model = clean_str(
        value_from_payload(payload, "model_id", model_id) or raw_model
    ) or clean_str(base_image_model)
    count_int = maybe_int(value_from_payload(payload, "count", count))

    size_value = clean_str(value_from_payload(payload, "size", size))
    aspect_ratio_value = clean_str(
        value_from_payload(payload, "aspect_ratio", aspect_ratio)
    )

    style_hint = clean_str(payload.get("style")) or "realistic"
    style_preset_id_value = clean_str(payload.get("style_preset_id"))
    style_spec_value = payload.get("style_spec")

    reference_images = coerce_str_list(payload.get("reference_images") or [])

    return VirtualIPVariantRequest(
        prompt=prompt_value,
        model=selected_model,
        count=count_int,
        size=size_value,
        aspect_ratio=aspect_ratio_value,
        style=style_hint,
        style_preset_id=style_preset_id_value,
        style_spec=style_spec_value,
        reference_images=reference_images,
    )


def build_virtual_ip_variant_task_payload(
    *,
    virtual_ip_id: int,
    virtual_ip_business_id: str | None,
    image_id: int,
    request: VirtualIPVariantRequest,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "virtual_ip_id": virtual_ip_id,
        "virtual_ip_business_id": virtual_ip_business_id,
        "image_id": image_id,
        "prompt": request.prompt,
        "model": request.model,
        "count": request.count,
        "size": request.size,
        "aspect_ratio": request.aspect_ratio,
        "style": request.style,
        "style_preset_id": request.style_preset_id,
        "style_spec": request.style_spec,
        "reference_images": request.reference_images,
    }
    return {k: v for k, v in payload.items() if v is not None}


async def generate_virtual_ip_image_variants(
    *,
    db: Session,
    virtual_ip: VirtualIP,
    base_image: VirtualIPImage,
    request: VirtualIPVariantRequest,
    backend_base: str,
    ai_service: Any,
    require_upload: bool,
) -> list[VirtualIPImage]:
    base_image_input = base_image.oss_url or base_image.file_path or ""

    final_prompt = render_virtual_ip_image_variant_prompt(
        character_name=virtual_ip.name,
        variant_prompt=request.prompt,
        character_description=virtual_ip.description,
        style=request.style,
        category=base_image.category,
        style_prompt=virtual_ip.style_prompt,
    )

    normalized = normalize_image_gen_request(
        ImageGenRequest(
            domain=ImageGenDomain.VIRTUAL_IP,
            mode=ImageGenMode.IMAGE_TO_IMAGE,
            prompt=final_prompt,
            model=request.model,
            style=request.style,
            style_preset_id=request.style_preset_id,
            style_spec=request.style_spec,
            count=request.count,
            size=request.size,
            aspect_ratio=request.aspect_ratio,
            base_image=base_image_input,
            reference_images=request.reference_images,
            backend_base=backend_base,
        ),
        strict=False,
    )

    call = build_ai_manager_call(normalized)
    if not call.get("image_url"):
        raise RuntimeError("基础图像地址缺失，无法执行图生图")

    response = await ai_service.ai_manager.image_to_image(**call)
    if not response.success:
        raise RuntimeError(response.error or "图生图生成失败")

    images = response.data.get("images", []) if isinstance(response.data, dict) else []
    if not images:
        raise RuntimeError("图生图接口未返回任何图像")

    generation_params = dict(response.usage or {})
    if isinstance(response.metadata, dict):
        if response.metadata.get("style_spec") is not None:
            generation_params["style_spec"] = response.metadata.get("style_spec")
        if response.metadata.get("style_spec_resolution") is not None:
            generation_params["style_spec_resolution"] = response.metadata.get(
                "style_spec_resolution"
            )
    if normalized.size is not None:
        generation_params["size"] = normalized.size
    if normalized.aspect_ratio is not None:
        generation_params["aspect_ratio"] = normalized.aspect_ratio

    extra_images = list(normalized.extra_images or [])
    image_gen_meta = {
        "domain": normalized.domain.value,
        "mode": normalized.mode.value,
        "provider": normalized.provider,
        "model_id": normalized.model_id,
        "size": normalized.size,
        "aspect_ratio": normalized.aspect_ratio,
        "reference_images_count": len(extra_images),
        "reference_images_hash": hash_reference_images(extra_images),
        "audit_warnings": list(normalized.audit.warnings or []),
    }

    created_images: list[VirtualIPImage] = []
    for idx, variant_url in enumerate(images):
        stored = await ai_service._persist_generated_image(
            image_data=variant_url,
            ip_name=virtual_ip.name,
            category=base_image.category or "portrait",
            prefix="ai-generated/virtual-ip",
            metadata={
                "virtual_ip_id": virtual_ip.id,
                "base_image_id": base_image.id,
                "provider": response.provider or normalized.provider,
                "model": normalized.model_id or response.model,
            },
            require_upload=require_upload,
        )

        image_data = VirtualIPImageCreate(
            virtual_ip_id=virtual_ip.id,
            file_path=stored.get("relative_path") or "",
            oss_url=stored.get("oss_url"),
            filename=stored.get("filename") or "",
            original_filename=f"{virtual_ip.name}_{base_image.category or 'variant'}_img2img_{idx + 1}.png",
            file_size=stored.get("file_size"),
            mime_type="image/png",
            category=base_image.category or "portrait",
            tags=[base_image.category or "portrait", "ai_generated", "variant"],
            prompt=normalized.prompt,
            ai_model=normalized.model_id or response.model,
            generation_params=generation_params,
            is_default=False,
            metadata={
                "generation_method": "image_to_image",
                "provider": response.provider,
                "model": response.model,
                "base_image_id": base_image.id,
                "base_image_url": normalized.base_image_url,
                "variant_url": variant_url,
                "oss_upload": stored.get("oss_upload"),
                "image_gen": image_gen_meta,
            },
        )

        db_image = VirtualIPImage(
            **image_data.model_dump(), virtual_ip_business_id=virtual_ip.business_id
        )
        db.add(db_image)
        created_images.append(db_image)

    db.commit()
    for img in created_images:
        db.refresh(img)
    return created_images
