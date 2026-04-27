"""
Story Structure helper functions.

Shared utilities for story structure endpoints including prompt composition,
reference image handling, and environment style sanitization.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from app.models.story_structure import Environment
from app.services.ai_service import ai_service
from app.services.providers.image_param_utils import compute_image_ui
from app.services.storage import oss_service
from app.utils.model_utils import is_openai_image_model
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def sanitize_environment_style_spec(_: Optional[dict]) -> Optional[dict]:
    """Environment generation does not pass style_spec to avoid character/shot style interference."""
    return None


def sanitize_environment_style(
    style: Optional[str], style_preset_id: Optional[str], style_spec: Optional[dict]
) -> tuple[str, None, None]:
    """
    Environment images do not use style_preset/style_spec to prevent character style interference.
    Only keep style as a lightweight hint, fallback to realistic.
    """
    style_clean = style or "realistic"
    return style_clean, None, None


def normalize_reference_images(refs: list[str], backend_base: str) -> list[str]:
    """Filter valid reference image URLs, avoid treating descriptive strings as image paths."""
    allowed_ext = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg")
    normalized: list[str] = []
    for raw in refs:
        if not isinstance(raw, str):
            continue
        ref_url = raw.strip()
        if not ref_url:
            continue
        lower = ref_url.lower()
        base_path = lower.split("?", 1)[0]
        if lower.startswith(("http://", "https://", "data:image/")):
            normalized.append(ref_url)
        elif base_path.endswith(allowed_ext):
            path = ref_url if ref_url.startswith("/") else f"/{ref_url}"
            normalized.append(f"{backend_base}{path}")
    return normalized


def infer_provider_from_model(model: Optional[str]) -> Optional[str]:
    """Infer AI provider from model name."""
    if not model:
        return None
    normalized = model.lower()
    if (
        normalized.startswith(("seedream", "volcengine"))
        or "doubao" in normalized
        or "seedream" in normalized
    ):
        return "volcengine"
    if normalized.startswith("deepseek"):
        return "deepseek"
    if normalized.startswith(("keling", "kling")):
        return "keling"
    if normalized.startswith("jimeng"):
        return "jimeng"
    if is_openai_image_model(normalized):
        return "openai"
    if normalized.startswith("gemini"):
        return "google"
    return None


def strip_provider_prefix(model: Optional[str]) -> Optional[str]:
    """Strip provider prefix from model name (e.g., 'openai:gpt-4' -> 'gpt-4')."""
    if not model:
        return None
    return model.split(":", 1)[1] if ":" in model else model


def resolve_image_aspect_ratio(
    provider: Optional[str],
    model: Optional[str],
    aspect_ratio: Optional[str],
) -> Optional[str]:
    """Return aspect ratio only when the provider/model supports it."""
    if not provider or not model or not aspect_ratio:
        return None
    ratio_value = aspect_ratio.strip() if isinstance(aspect_ratio, str) else ""
    if not ratio_value:
        return None
    try:
        rules = compute_image_ui(provider, model)
    except Exception:
        return None
    return ratio_value if rules.supports_aspect_ratio else None


def compose_environment_prompt(env, extra: Optional[str] = None) -> str:
    """Compose a richer prompt for environment generation using name/description/tags/category."""
    parts: List[str] = []
    if env.name:
        parts.append(f"Environment: {env.name}")
    if env.category:
        parts.append(f"Category: {env.category}")
    if env.tags:
        tags_str = ", ".join([t for t in env.tags if t])
        if tags_str:
            parts.append(f"Tags: {tags_str}")
    if env.description:
        parts.append(f"Description: {env.description}")
    # Default structured guidance for overall-to-detail, indoor/outdoor layers
    category_hint = (
        "室内布局、光线、材质细节"
        if (env.category or "").lower() == "indoor"
        else "室外空间、天气、周边环境"
    )
    parts.append(
        f"Overall-to-detail: 开场远景交代空间 -> 中景展示主要区域 -> 近景刻画关键道具/纹理；"
        f"Environment focus: {category_hint}；保持真实光影和透视，色彩和风格统一。"
    )
    if extra:
        extra_clean = extra.strip()
        desc_clean = (env.description or "").strip()
        # Avoid duplicating extra prompt if identical to description
        if extra_clean and extra_clean.lower() != desc_clean.lower():
            parts.append(extra_clean)
    if not parts:
        return "Environment scene with clear spatial layout and lighting cues"
    return " | ".join(parts)


async def download_and_attach(db: Session, env, image_urls: List[str]) -> List[str]:
    """Download images and attach to environment reference_images."""
    saved: List[str] = []
    errors: List[str] = []
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
                require_upload=bool(oss_service),
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
    # Force persist JSON column to avoid untracked list modifications being lost
    db.query(Environment).filter(Environment.id == env.id).update(
        {"reference_images": env.reference_images}
    )
    # Commit persistence to ensure subsequent GET /environments/{id}/images sees new refs
    db.commit()
    return saved


def resolve_environment_url(base: str, backend_base: str) -> str:
    """Resolve base image to full URL."""
    if isinstance(base, str) and base.startswith("http"):
        return base
    path = base if isinstance(base, str) else ""
    if path and not path.startswith("/"):
        path = "/" + path
    return f"{backend_base}{path}"
