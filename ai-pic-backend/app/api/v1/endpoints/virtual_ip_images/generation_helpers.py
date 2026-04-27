"""
Virtual IP image generation helpers.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.prompts.template_audit import build_prompt_template_audit
from app.schemas.virtual_ip import VirtualIPImageCreate
from app.services.ai_service import ai_service
from app.services.image_gen.coerce import clean_str, maybe_float, maybe_int
from app.utils.model_utils import DEFAULT_OPENAI_IMAGE_MODEL
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from .helpers import not_deleted, set_ip_default_avatar


async def read_request_payload(request: Request) -> Dict[str, Any]:
    """Read JSON payload when content-type is application/json."""
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        try:
            return await request.json()
        except Exception:
            return {}
    return {}


def resolve_virtual_ip_image_params(
    payload: Dict[str, Any],
    *,
    style: Optional[str],
    category: Optional[str],
    model: Optional[str],
    model_id: Optional[str],
    additional_prompts: Optional[str],
    is_default: Optional[str | bool],
    count: Optional[int],
    size: Optional[str],
    aspect_ratio: Optional[str],
    seed: Optional[int],
    steps: Optional[int],
    cfg_scale: Optional[float],
    negative_prompt: Optional[str],
    generation_profile: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve image generation parameters from payload + form defaults."""
    style_value = payload.get("style", style) or "realistic"
    style_preset_id = payload.get("style_preset_id")
    style_spec = payload.get("style_spec")
    category_value = payload.get("category", category) or "portrait"
    raw_model = payload.get("model", model)
    selected_model = (
        payload.get("model_id") or model_id or raw_model or DEFAULT_OPENAI_IMAGE_MODEL
    ).strip()
    if not selected_model:
        selected_model = DEFAULT_OPENAI_IMAGE_MODEL

    count_value = payload.get("count", count)
    size_value = payload.get("size", size)
    aspect_ratio_value = payload.get("aspect_ratio", aspect_ratio)
    seed_int = maybe_int(payload.get("seed", seed))
    steps_int = maybe_int(payload.get("steps", steps))
    cfg_scale_value = maybe_float(payload.get("cfg_scale", cfg_scale))
    negative_prompt_value = clean_str(payload.get("negative_prompt", negative_prompt))
    generation_profile_value = clean_str(
        payload.get("generation_profile", generation_profile)
    )
    additional_raw = payload.get("additional_prompts", additional_prompts) or ""
    is_default_value = payload.get("is_default", is_default)
    additional_prompt_list = [
        item.strip() for item in additional_raw.split(",") if item.strip()
    ]
    try:
        count_int = int(count_value) if count_value is not None else 1
    except (TypeError, ValueError):
        count_int = 1
    if count_int < 1:
        count_int = 1
    is_default_bool = False
    if isinstance(is_default_value, bool):
        is_default_bool = is_default_value
    elif isinstance(is_default_value, str):
        is_default_bool = is_default_value.lower() in {"true", "1", "yes", "on"}

    return {
        "style": style_value,
        "style_preset_id": (style_preset_id or "").strip() or None,
        "style_spec": style_spec,
        "category": category_value,
        "model": selected_model,
        "count": count_int,
        "size": size_value,
        "aspect_ratio": aspect_ratio_value,
        "seed": seed_int,
        "steps": steps_int,
        "cfg_scale": cfg_scale_value,
        "negative_prompt": negative_prompt_value,
        "generation_profile": generation_profile_value,
        "additional_prompts": additional_prompt_list,
        "is_default": is_default_bool,
    }


def build_virtual_ip_appearance_description(virtual_ip: VirtualIP) -> str:
    """Build appearance-only description for image generation."""
    parts: List[str] = []
    if virtual_ip.description:
        parts.append(str(virtual_ip.description).strip())
    style_prompt = getattr(virtual_ip, "style_prompt", None)
    if style_prompt:
        parts.append(str(style_prompt).strip())
    return "，".join([p for p in parts if p])


async def run_virtual_ip_image_generation(
    virtual_ip_id: str,
    virtual_ip: VirtualIP,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """Call AI service to generate virtual IP image."""
    try:
        from app.core.logging import get_logger

        get_logger().info(
            "VirtualIP image gen | ip=%s model=%s style=%s category=%s prompts=%s",
            virtual_ip_id,
            params["model"],
            params["style"],
            params["category"],
            ", ".join(params.get("additional_prompts") or []),
        )
    except Exception:
        pass

    aggregated_description = build_virtual_ip_appearance_description(virtual_ip)
    result = await ai_service.generate_virtual_ip_image(
        ip_name=virtual_ip.name,
        description=aggregated_description,
        style=params["style"],
        style_preset_id=params["style_preset_id"],
        style_spec=params["style_spec"],
        category=params["category"],
        model=params["model"],
        additional_prompts=params["additional_prompts"],
        background_story=None,
        count=params["count"],
        size=params["size"],
        aspect_ratio=params["aspect_ratio"],
        generation_profile=params.get("generation_profile"),
        seed=params.get("seed"),
        steps=params.get("steps"),
        cfg_scale=params.get("cfg_scale"),
        negative_prompt=params.get("negative_prompt"),
    )

    if not result:
        raise HTTPException(status_code=500, detail="AI图像生成失败")
    return result


def build_virtual_ip_image_payload(
    virtual_ip: VirtualIP, params: Dict[str, Any]
) -> Dict[str, Any]:
    """Build task payload for Celery worker."""
    aggregated_description = build_virtual_ip_appearance_description(virtual_ip)
    return {
        "virtual_ip_id": virtual_ip.id,
        "virtual_ip_business_id": getattr(virtual_ip, "business_id", None),
        "virtual_ip_name": virtual_ip.name,
        "aggregated_description": aggregated_description,
        "style": params["style"],
        "style_preset_id": params["style_preset_id"],
        "style_spec": params["style_spec"],
        "category": params["category"],
        "model": params["model"],
        "count": params["count"],
        "size": params["size"],
        "aspect_ratio": params["aspect_ratio"],
        "generation_profile": params.get("generation_profile"),
        "seed": params.get("seed"),
        "steps": params.get("steps"),
        "cfg_scale": params.get("cfg_scale"),
        "negative_prompt": params.get("negative_prompt"),
        "additional_prompts": params["additional_prompts"],
        "is_default": params["is_default"],
        "prompt_template": build_prompt_template_audit("virtual_ip_image"),
    }


def build_virtual_ip_image_tags(
    style: str,
    category: str,
    additional_prompts: List[str],
    generation_method: str,
) -> List[str]:
    """Build tags for generated images."""
    tags = [style, category, "ai_generated", generation_method]
    if additional_prompts:
        tags.extend(additional_prompts)
    return tags


def resolve_local_image_info(result: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve local file details for generated image."""
    local_file_path = result.get("local_file_path")
    if not local_file_path or not os.path.exists(local_file_path):
        raise HTTPException(status_code=500, detail="图像文件生成失败")
    file_size = os.path.getsize(local_file_path)
    filename = os.path.basename(local_file_path)
    relative_path = result.get("relative_path") or f"/uploads/{filename}"
    oss_upload = result.get("oss_upload") or {}
    oss_url = result.get("oss_url") or oss_upload.get("file_url")
    return {
        "local_file_path": local_file_path,
        "file_size": file_size,
        "filename": filename,
        "relative_path": relative_path,
        "oss_url": oss_url,
    }


def build_generation_params(
    result: Dict[str, Any],
    size_value: Optional[str],
    aspect_ratio_value: Optional[str],
) -> Dict[str, Any]:
    """Assemble generation params for metadata."""
    params = dict(result.get("usage") or {})
    if result.get("style_preset_id") is not None:
        params["style_preset_id"] = result.get("style_preset_id")
    if result.get("style_spec") is not None:
        params["style_spec"] = result.get("style_spec")
    if result.get("style_spec_resolution") is not None:
        params["style_spec_resolution"] = result.get("style_spec_resolution")
    if "size" in result:
        params["size"] = result.get("size")
    elif size_value is not None:
        params["size"] = size_value

    if "aspect_ratio" in result:
        params["aspect_ratio"] = result.get("aspect_ratio")
    elif aspect_ratio_value is not None:
        params["aspect_ratio"] = aspect_ratio_value

    for dim_key in ("width", "height"):
        dim_value = result.get(dim_key)
        if dim_value is not None:
            params[dim_key] = dim_value
    if result.get("prompt_template") is not None:
        params["prompt_template"] = result.get("prompt_template")
    if result.get("prompt_sha256") is not None:
        params["prompt_sha256"] = result.get("prompt_sha256")
    return params


def build_virtual_ip_image_metadata(
    result: Dict[str, Any],
    style: str,
    additional_prompts: List[str],
    local_file_path: str,
) -> Dict[str, Any]:
    """Build metadata payload for generated images."""
    return {
        "generation_method": result["generation_method"],
        "prompt": result["prompt"],
        "prompt_template": result.get("prompt_template"),
        "prompt_sha256": result.get("prompt_sha256"),
        "style": style,
        "additional_prompts": additional_prompts,
        "original_openai_url": result.get("original_image_url", ""),
        "local_file_path": local_file_path,
        "oss_upload": result.get("oss_upload"),
    }


def clear_default_virtual_ip_image(db: Session, virtual_ip_id: int) -> None:
    """Reset existing default images for a virtual IP."""
    not_deleted(db.query(VirtualIPImage), VirtualIPImage).filter(
        VirtualIPImage.virtual_ip_id == virtual_ip_id,
        VirtualIPImage.is_default.is_(True),
    ).update({"is_default": False})


def persist_virtual_ip_image(
    db: Session,
    virtual_ip: VirtualIP,
    result: Dict[str, Any],
    params: Dict[str, Any],
) -> VirtualIPImage:
    """Persist generated image and return the ORM instance."""
    if params.get("is_default"):
        clear_default_virtual_ip_image(db, virtual_ip.id)

    tags = build_virtual_ip_image_tags(
        params["style"],
        params["category"],
        params.get("additional_prompts") or [],
        result["generation_method"],
    )
    file_info = resolve_local_image_info(result)
    generation_params = build_generation_params(
        result,
        params.get("size"),
        params.get("aspect_ratio"),
    )
    generation_profile_value = result.get("generation_profile")
    if generation_profile_value is not None:
        generation_params["generation_profile"] = generation_profile_value
    for key in ("seed", "steps", "cfg_scale", "negative_prompt"):
        value = result.get(key)
        if value is None:
            value = params.get(key)
        if value is not None:
            generation_params[key] = value

    image_data = VirtualIPImageCreate(
        virtual_ip_id=virtual_ip.id,
        file_path=file_info["relative_path"],
        oss_url=file_info["oss_url"],
        filename=file_info["filename"],
        original_filename=f"{virtual_ip.name}_{params['category']}_generated.png",
        file_size=file_info["file_size"],
        mime_type="image/png",
        category=params["category"],
        tags=tags,
        prompt=result["prompt"],
        ai_model=result["model_used"],
        generation_params=generation_params,
        is_default=params.get("is_default", False),
        metadata=build_virtual_ip_image_metadata(
            result,
            params["style"],
            params.get("additional_prompts") or [],
            file_info["local_file_path"],
        ),
    )

    db_image = VirtualIPImage(
        **image_data.dict(), virtual_ip_business_id=virtual_ip.business_id
    )
    db.add(db_image)
    if params.get("is_default"):
        set_ip_default_avatar(db, virtual_ip.id, db_image)
    db.commit()
    db.refresh(db_image)
    return db_image
