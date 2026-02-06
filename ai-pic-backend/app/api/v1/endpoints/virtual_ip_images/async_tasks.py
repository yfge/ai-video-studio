"""
Virtual IP Images background task processors.

Celery worker functions for async image generation.
"""

import os
from typing import Any, Dict

from app.models.task import Task, TaskStatus
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.schemas.virtual_ip import VirtualIPImageCreate
from app.services.ai_service import ai_service

from .helpers import set_ip_default_avatar


def process_virtual_ip_image_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """Celery worker function for virtual IP text-to-image generation.

    Logic mirrors the sync endpoint generate_virtual_ip_image:
    - Call AIService.generate_virtual_ip_image
    - Create VirtualIPImage record
    - Update Task status
    """
    from app.core.database import get_task_db

    with get_task_db() as db:
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.PROCESSING
                db.commit()

            virtual_ip = (
                db.query(VirtualIP)
                .filter(VirtualIP.id == payload["virtual_ip_id"])
                .first()
            )
            if not virtual_ip:
                raise RuntimeError("虚拟IP不存在")

            import anyio

            created_image = anyio.run(
                lambda: _generate_and_persist_image(db, virtual_ip, payload)
            )
            if task:
                task.status = TaskStatus.COMPLETED
                task.result_file_path = (
                    f"virtual_ip_image:"
                    f"{created_image.virtual_ip_id}:{created_image.id}"
                )
                db.commit()
        except Exception as exc:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(exc)
                db.commit()


async def _generate_and_persist_image(
    db, virtual_ip: VirtualIP, payload: Dict[str, Any]
) -> VirtualIPImage:
    """Call AI service and persist the generated image record."""
    result = await ai_service.generate_virtual_ip_image(
        ip_name=payload.get("virtual_ip_name") or virtual_ip.name,
        description=(
            payload.get("aggregated_description")
            or virtual_ip.description
            or ""
        ),
        style=payload.get("style") or "realistic",
        style_preset_id=payload.get("style_preset_id"),
        style_spec=payload.get("style_spec"),
        category=payload.get("category") or "portrait",
        model=payload.get("model") or "dalle-3",
        additional_prompts=payload.get("additional_prompts") or [],
        background_story=None,
        count=int(payload.get("count") or 1),
        size=payload.get("size"),
        aspect_ratio=payload.get("aspect_ratio"),
        generation_profile=payload.get("generation_profile"),
        seed=payload.get("seed"),
        steps=payload.get("steps"),
        cfg_scale=payload.get("cfg_scale"),
        negative_prompt=payload.get("negative_prompt"),
        reference_images=payload.get("reference_images") or None,
    )
    if not result:
        raise RuntimeError("AI图像生成失败")

    additional_prompts_list = payload.get("additional_prompts") or []
    is_default_bool = bool(payload.get("is_default"))

    if is_default_bool:
        db.query(VirtualIPImage).filter(
            VirtualIPImage.virtual_ip_id == virtual_ip.id,
            VirtualIPImage.is_default.is_(True),
        ).update({"is_default": False})

    tags = [
        payload.get("style") or "realistic",
        payload.get("category") or "portrait",
        "ai_generated",
        result["generation_method"],
    ]
    if additional_prompts_list:
        tags.extend(additional_prompts_list)

    local_file_path = result.get("local_file_path")
    if not local_file_path or not os.path.exists(local_file_path):
        raise RuntimeError("图像文件生成失败")

    file_size = os.path.getsize(local_file_path)
    filename = os.path.basename(local_file_path)
    relative_path = result.get("relative_path") or f"/uploads/{filename}"
    oss_upload = result.get("oss_upload") or {}
    oss_url = result.get("oss_url") or oss_upload.get("file_url")

    generation_params = _build_generation_params(result, payload)

    prompt_template = result.get("prompt_template") or payload.get(
        "prompt_template"
    )
    image_data = VirtualIPImageCreate(
        virtual_ip_id=virtual_ip.id,
        file_path=relative_path,
        oss_url=oss_url,
        filename=filename,
        original_filename=(
            f"{virtual_ip.name}_{payload.get('category') or 'portrait'}"
            f"_generated.png"
        ),
        file_size=file_size,
        mime_type="image/png",
        category=payload.get("category") or "portrait",
        tags=tags,
        prompt=result["prompt"],
        ai_model=result["model_used"],
        generation_params=generation_params,
        is_default=is_default_bool,
        metadata={
            "generation_method": result["generation_method"],
            "prompt": result["prompt"],
            "prompt_template": prompt_template,
            "prompt_sha256": result.get("prompt_sha256"),
            "style": result["style"],
            "additional_prompts": additional_prompts_list,
            "size": generation_params.get("size"),
            "aspect_ratio": generation_params.get("aspect_ratio"),
            "width": result.get("width"),
            "height": result.get("height"),
            "original_openai_url": result.get("original_image_url", ""),
            "local_file_path": local_file_path,
            "oss_upload": result.get("oss_upload"),
        },
    )

    db_image = VirtualIPImage(
        **image_data.dict(), virtual_ip_business_id=virtual_ip.business_id
    )
    db.add(db_image)
    if is_default_bool:
        set_ip_default_avatar(db, virtual_ip.id, db_image)
    db.commit()
    db.refresh(db_image)
    return db_image


def _build_generation_params(
    result: Dict[str, Any], payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Extract and merge generation parameters from result and payload."""
    generation_params = dict(result.get("usage") or {})
    for key in ("style_preset_id", "style_spec", "style_spec_resolution"):
        if result.get(key) is not None:
            generation_params[key] = result.get(key)

    for key in ("size", "aspect_ratio"):
        if key in result:
            generation_params[key] = result[key]
        elif payload.get(key) is not None:
            generation_params[key] = payload[key]

    for dim_key in ("width", "height"):
        dim_value = result.get(dim_key)
        if dim_value is not None:
            generation_params[dim_key] = dim_value

    prompt_template = result.get("prompt_template") or payload.get(
        "prompt_template"
    )
    if prompt_template is not None:
        generation_params["prompt_template"] = prompt_template
    if result.get("prompt_sha256") is not None:
        generation_params["prompt_sha256"] = result.get("prompt_sha256")
    generation_profile_value = result.get("generation_profile")
    if generation_profile_value is not None:
        generation_params["generation_profile"] = generation_profile_value
    for key in ("seed", "steps", "cfg_scale", "negative_prompt"):
        value = result.get(key)
        if value is None:
            value = payload.get(key)
        if value is not None:
            generation_params[key] = value

    return generation_params
