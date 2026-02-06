"""
Virtual IP Images img2img background task processor.

Celery worker function for async variant generation.
"""

from __future__ import annotations

from typing import Any, Dict

from app.core.config import settings
from app.models.task import Task, TaskStatus
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.services.ai_service import ai_service
from app.services.storage import oss_service
from app.services.virtual_ip.image_variant_requests import (
    resolve_virtual_ip_variant_request,
)
from app.services.virtual_ip.image_variant_service import (
    generate_virtual_ip_image_variants,
)


def process_virtual_ip_image_variant_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """Celery worker function for virtual IP image-to-image generation."""
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

            if not ai_service.ai_manager:
                raise RuntimeError("AI管理器未初始化，无法执行图生图")

            backend_base = (
                getattr(settings, "INTERNAL_BACKEND_URL", None)
                or "http://localhost:8000"
            ).rstrip("/")

            import anyio

            async def _run() -> list[VirtualIPImage]:
                request = resolve_virtual_ip_variant_request(
                    payload,
                    prompt=None,
                    model=None,
                    model_id=None,
                    count=None,
                    size=None,
                    aspect_ratio=None,
                    seed=None,
                    steps=None,
                    cfg_scale=None,
                    negative_prompt=None,
                    strength=None,
                    base_image_model=base_image.ai_model,
                )
                return await generate_virtual_ip_image_variants(
                    db=db,
                    virtual_ip=virtual_ip,
                    base_image=base_image,
                    request=request,
                    backend_base=backend_base,
                    ai_service=ai_service,
                    require_upload=bool(oss_service),
                )

            created_images = anyio.run(_run)

            if task:
                task.status = TaskStatus.COMPLETED
                task.result_file_path = (
                    f"virtual_ip_image_variants:{payload['image_id']}"
                    f":{len(created_images)}"
                )
                db.commit()
        except Exception as exc:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(exc)
                db.commit()
