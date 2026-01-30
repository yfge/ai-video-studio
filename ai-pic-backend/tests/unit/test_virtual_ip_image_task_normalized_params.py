from __future__ import annotations

from pathlib import Path

import pytest
from app.api.v1.endpoints.virtual_ip_images.async_tasks import (
    process_virtual_ip_image_task,
)
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPImage


@pytest.mark.unit
def test_process_virtual_ip_image_task_persists_normalized_dimensions(
    test_db, monkeypatch, tmp_path: Path
):
    import app.core.database as database

    monkeypatch.setattr(database, "SessionLocal", test_db)

    session = test_db()
    user = User(
        username="u1",
        email="u1@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    session.add(user)
    session.flush()
    user_id = user.id

    vip = VirtualIP(user_id=user.id, name="VIP", description="desc")
    session.add(vip)
    session.flush()
    vip_id = vip.id
    vip_name = vip.name

    task = Task(
        title="虚拟IP文生图 - VIP",
        description="异步生成虚拟IP图像",
        task_type=TaskType.VIRTUAL_IP_IMAGE_GENERATION,
        status=TaskStatus.PENDING,
        prompt="VirtualIP image gen for VIP",
        parameters="{}",
        user_id=user.id,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    task_id = task.id
    session.close()

    image_path = tmp_path / "out.png"
    image_path.write_bytes(b"png")

    async def _fake_generate_virtual_ip_image(**_kwargs):
        return {
            "prompt": "p",
            "style": "realistic",
            "model_used": "dall-e-3",
            "generation_method": "openai_dalle",
            "local_file_path": str(image_path),
            "relative_path": "/uploads/out.png",
            "oss_url": None,
            "oss_upload": None,
            # Normalized values (dall-e-3 does not support 2K -> 1024x1024 fallback).
            "size": "1024x1024",
            "aspect_ratio": None,
            "width": 1024,
            "height": 1024,
            "usage": {},
        }

    import app.api.v1.endpoints.virtual_ip_images.async_tasks as vip_async

    monkeypatch.setattr(
        vip_async.ai_service,
        "generate_virtual_ip_image",
        _fake_generate_virtual_ip_image,
    )

    payload = {
        "virtual_ip_id": vip_id,
        "virtual_ip_name": vip_name,
        "aggregated_description": "desc",
        "style": "realistic",
        "category": "portrait",
        "model": "dalle-3",
        "count": 1,
        # Raw (pre-normalized) inputs
        "size": "2K",
        "aspect_ratio": "1:1",
        "additional_prompts": [],
        "is_default": False,
        "prompt_template": {"name": "virtual_ip_image"},
    }

    process_virtual_ip_image_task(task_id, payload, user_id)

    session = test_db()
    try:
        image = (
            session.query(VirtualIPImage)
            .filter(VirtualIPImage.virtual_ip_id == vip_id)
            .order_by(VirtualIPImage.id.desc())
            .first()
        )
        assert image is not None
        assert image.generation_params is not None
        assert image.generation_params["size"] == "1024x1024"
        assert image.generation_params["width"] == 1024
        assert image.generation_params["height"] == 1024
        assert image.generation_params["aspect_ratio"] is None

        refreshed_task = session.query(Task).filter(Task.id == task_id).first()
        assert refreshed_task is not None
        assert refreshed_task.status == TaskStatus.COMPLETED
    finally:
        session.close()
