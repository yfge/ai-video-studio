from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from app.models.story_structure import Environment
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


async def persist_environment_images(
    *,
    db: Session,
    env: Environment,
    image_urls: Sequence[str],
    ai_service: Any,
    require_upload: bool,
) -> list[str]:
    """Download generated images and attach them to Environment.reference_images.

    Uses a direct UPDATE to ensure JSON column changes are persisted.
    """
    saved: list[str] = []
    errors: list[str] = []
    for image_url in image_urls:
        try:
            stored = await ai_service._persist_generated_image(
                image_data=image_url,
                ip_name=env.name or f"environment-{env.id}",
                category="environment",
                prefix="ai-generated/environments",
                metadata={
                    "environment_id": env.id,
                    "environment_name": env.name or "",
                },
                require_upload=require_upload,
            )
        except Exception as exc:
            errors.append(f"{image_url}: {exc}")
            logger.warning(
                "环境图像持久化失败 | env_id=%s image_url=%s error=%s",
                getattr(env, "id", None),
                image_url,
                exc,
            )
            continue

        final_url = stored.get("oss_url") or stored.get("relative_path")
        if not final_url:
            errors.append(f"{image_url}: missing persisted URL")
            logger.warning(
                "环境图像未返回可用路径 | env_id=%s image_url=%s stored=%s",
                getattr(env, "id", None),
                image_url,
                stored,
            )
            continue
        saved.append(final_url)

    if not saved:
        detail = errors[0] if errors else "未找到可用的持久化结果"
        raise RuntimeError(f"环境图像持久化失败: {detail}")

    refs = env.reference_images or []
    refs.extend(saved)
    env.reference_images = refs

    db.query(Environment).filter(Environment.id == env.id).update(
        {"reference_images": env.reference_images}
    )
    db.commit()
    return saved
