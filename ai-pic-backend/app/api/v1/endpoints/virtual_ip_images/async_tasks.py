"""
Virtual IP Images background task processors.

Celery worker functions for async image generation.
"""

import os
from typing import Any, Dict

from app.core.config import settings
from app.models.task import Task, TaskStatus
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.schemas.virtual_ip import VirtualIPImageCreate
from app.services.ai_service import ai_service
from app.services.storage import oss_service
from app.utils.model_utils import infer_provider_from_model
from .helpers import normalize_reference_images, set_ip_default_avatar


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


def process_virtual_ip_image_variant_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """Celery worker function for virtual IP image-to-image generation.

    Logic mirrors the sync endpoint generate_virtual_ip_image_variant:
    - Call AIServiceManager.image_to_image
    - Persist via AIService._persist_generated_image
    - Create VirtualIPImage records
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

        base_image = (
            db.query(VirtualIPImage)
            .filter(
                VirtualIPImage.id == payload["image_id"],
                VirtualIPImage.virtual_ip_id == payload["virtual_ip_id"],
            )
            .first()
        )
        if not base_image:
            raise RuntimeError("基础图像不存在")

        import anyio

        async def _run() -> list[VirtualIPImage]:
            # Build image URL: prefer OSS, fallback to local
            if base_image.oss_url:
                image_url = base_image.oss_url
            else:
                file_path = base_image.file_path or ""
                if file_path and not file_path.startswith("/"):
                    file_path = "/" + file_path
                backend_base = (
                    getattr(settings, "INTERNAL_BACKEND_URL", None)
                    or "http://localhost:8000"
                ).rstrip("/")
                image_url = f"{backend_base}{file_path}"

            selected_model = payload.get("model") or base_image.ai_model or ""
            prompt_value = payload.get("prompt") or (
                "为当前角色生成不同视角/姿态的图像，如背面照或全身照"
            )
            count_int = int(payload.get("count") or 1)
            size_value = payload.get("size")
            aspect_ratio_value = payload.get("aspect_ratio")
            style_hint = payload.get("style") or "realistic"
            style_preset_id = payload.get("style_preset_id")
            style_spec = payload.get("style_spec")
            prefer_provider = infer_provider_from_model(selected_model or "")

            if not ai_service.ai_manager:
                raise RuntimeError("AI管理器未初始化，无法执行图生图")

            # Normalize reference images
            reference_images = payload.get("reference_images") or []
            backend_base = (
                getattr(settings, "INTERNAL_BACKEND_URL", None)
                or "http://localhost:8000"
            ).rstrip("/")
            extra_images = normalize_reference_images(reference_images, backend_base)

            response = await ai_service.ai_manager.image_to_image(
                image_url=image_url,
                prompt=prompt_value,
                model=selected_model or None,
                prefer_provider=prefer_provider,
                count=count_int,
                size=size_value,
                aspect_ratio=aspect_ratio_value,
                style=style_hint,
                style_preset_id=style_preset_id,
                style_spec=style_spec,
                extra_images=extra_images,
            )
            if not response.success:
                raise RuntimeError(response.error or "图生图生成失败")

            images = (
                response.data.get("images", [])
                if isinstance(response.data, dict)
                else []
            )
            if not images:
                raise RuntimeError("图生图接口未返回任何图像")

            generation_params = dict(response.usage or {})
            if isinstance(response.metadata, dict):
                if response.metadata.get("style_spec") is not None:
                    generation_params["style_spec"] = response.metadata.get(
                        "style_spec"
                    )
                if response.metadata.get("style_spec_resolution") is not None:
                    generation_params["style_spec_resolution"] = response.metadata.get(
                        "style_spec_resolution"
                    )
            if size_value is not None:
                generation_params["size"] = size_value
            if aspect_ratio_value is not None:
                generation_params["aspect_ratio"] = aspect_ratio_value

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
                        "prompt": prompt_value,
                        "provider": response.provider,
                        "model": selected_model or response.model,
                    },
                    require_upload=bool(oss_service),
                )

                local_file_path = stored.get("local_file_path")
                if not local_file_path or not os.path.exists(local_file_path):
                    raise RuntimeError("图生图文件下载失败")

                file_size = stored.get("file_size") or os.path.getsize(local_file_path)
                filename = stored.get("filename") or os.path.basename(local_file_path)
                relative_path = stored.get("relative_path") or f"/uploads/{filename}"
                oss_result = stored.get("oss_upload")
                oss_url = stored.get("oss_url")

                tags = [
                    base_image.category or "portrait",
                    "ai_generated",
                    "variant",
                ]

                image_data = VirtualIPImageCreate(
                    virtual_ip_id=virtual_ip.id,
                    file_path=relative_path,
                    oss_url=oss_url,
                    filename=filename,
                    original_filename=f"{virtual_ip.name}_{base_image.category or 'variant'}_img2img_{idx + 1}.png",
                    file_size=file_size,
                    mime_type="image/png",
                    category=base_image.category or "portrait",
                    tags=tags,
                    prompt=prompt_value,
                    ai_model=selected_model or response.model,
                    generation_params=generation_params,
                    is_default=False,
                    metadata={
                        "generation_method": "image_to_image",
                        "provider": response.provider,
                        "model": response.model,
                        "base_image_id": base_image.id,
                        "base_image_url": image_url,
                        "variant_url": variant_url,
                        "oss_upload": oss_result,
                    },
                )

                db_image = VirtualIPImage(
                    **image_data.dict(), virtual_ip_business_id=virtual_ip.business_id
                )
                db.add(db_image)
                created_images.append(db_image)

            db.commit()
            for img in created_images:
                db.refresh(img)
            return created_images

        created_images = anyio.run(_run)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = (
                f"virtual_ip_image_variants:{payload['image_id']}:{len(created_images)}"
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
