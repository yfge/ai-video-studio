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
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        virtual_ip = (
            db.query(VirtualIP).filter(VirtualIP.id == payload["virtual_ip_id"]).first()
        )
        if not virtual_ip:
            raise RuntimeError("虚拟IP不存在")

        import anyio

        async def _run() -> VirtualIPImage:
            result = await ai_service.generate_virtual_ip_image(
                ip_name=payload.get("virtual_ip_name") or virtual_ip.name,
                description=payload.get("aggregated_description")
                or virtual_ip.description
                or "",
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
                seed=payload.get("seed"),
                steps=payload.get("steps"),
                cfg_scale=payload.get("cfg_scale"),
                negative_prompt=payload.get("negative_prompt"),
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
            oss_url = result.get("oss_url") or result.get("oss_upload", {}).get(
                "file_url"
            )

            generation_params = dict(result.get("usage") or {})
            if result.get("style_preset_id") is not None:
                generation_params["style_preset_id"] = result.get("style_preset_id")
            if result.get("style_spec") is not None:
                generation_params["style_spec"] = result.get("style_spec")
            if result.get("style_spec_resolution") is not None:
                generation_params["style_spec_resolution"] = result.get(
                    "style_spec_resolution"
                )
            if payload.get("size") is not None:
                generation_params["size"] = payload.get("size")
            if payload.get("aspect_ratio") is not None:
                generation_params["aspect_ratio"] = payload.get("aspect_ratio")
            prompt_template = result.get("prompt_template") or payload.get(
                "prompt_template"
            )
            if prompt_template is not None:
                generation_params["prompt_template"] = prompt_template
            if result.get("prompt_sha256") is not None:
                generation_params["prompt_sha256"] = result.get("prompt_sha256")
            for key in ("seed", "steps", "cfg_scale", "negative_prompt"):
                value = result.get(key)
                if value is None:
                    value = payload.get(key)
                if value is not None:
                    generation_params[key] = value

            image_data = VirtualIPImageCreate(
                virtual_ip_id=virtual_ip.id,
                file_path=relative_path,
                oss_url=oss_url,
                filename=filename,
                original_filename=f"{virtual_ip.name}_{payload.get('category') or 'portrait'}_generated.png",
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

        created_image = anyio.run(_run)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = (
                f"virtual_ip_image:{created_image.virtual_ip_id}:{created_image.id}"
            )
            db.commit()
    except Exception as exc:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            db.commit()
    finally:
        db.close()
