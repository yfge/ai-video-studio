"""
Story Structure background task processors.

Celery worker functions for async environment image generation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from app.core.config import settings
from app.models.task import Task, TaskStatus
from app.services import story_structure_service as svc
from app.services.ai_service import ai_service
from app.utils.model_utils import normalize_openai_image_style, parse_model_and_provider

from .helpers import (
    compose_environment_prompt,
    download_and_attach,
    infer_provider_from_model,
    normalize_reference_images,
    resolve_image_aspect_ratio,
    resolve_environment_url,
    sanitize_environment_style,
    strip_provider_prefix,
)


def process_environment_image_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """Celery worker function for environment text-to-image generation."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        env = svc.resolve_environment(db, payload["env_id"])
        if not env:
            raise RuntimeError("environment not found")

        import anyio

        async def _run() -> list[str]:
            prefer_provider: Optional[str] = None
            selected_model_raw = (payload.get("model") or "").strip() or None
            selected_model, prefer_provider_from_model = parse_model_and_provider(
                selected_model_raw
            )
            count_int = int(payload.get("count") or 1)
            size_value = payload.get("size")
            aspect_ratio_value = payload.get("aspect_ratio")
            style_hint, style_preset_id, style_spec = sanitize_environment_style(
                payload.get("style"),
                payload.get("style_preset_id"),
                payload.get("style_spec"),
            )

            prefer_provider_local = prefer_provider or prefer_provider_from_model
            prefer_provider_local = prefer_provider_local or infer_provider_from_model(
                selected_model or ""
            )
            if (prefer_provider_local or "").lower() == "openai":
                style_hint_local = normalize_openai_image_style(style_hint)
            else:
                style_hint_local = style_hint

            aspect_ratio_value = resolve_image_aspect_ratio(
                prefer_provider_local,
                strip_provider_prefix(selected_model),
                aspect_ratio_value,
            )
            final_prompt = compose_environment_prompt(env, payload.get("extra_prompt"))

            response = await ai_service.ai_manager.generate_image(
                prompt=final_prompt,
                model=strip_provider_prefix(selected_model),
                n=max(1, min(count_int, 4)),
                size=size_value,
                aspect_ratio=aspect_ratio_value,
                prefer_provider=prefer_provider_local,
                style=style_hint_local,
                style_preset_id=style_preset_id,
                style_spec=style_spec,
            )
            if not response.success:
                raise RuntimeError(response.error or "环境文生图生成失败")
            images = (
                response.data.get("images", [])
                if isinstance(response.data, dict)
                else []
            )
            if not images:
                raise RuntimeError("环境文生图接口未返回任何图像")

            saved_urls = await download_and_attach(db, env, images)
            response_meta = getattr(response, "metadata", None)
            if not isinstance(response_meta, dict):
                response_meta = {}
            extra = dict(env.extra_metadata or {})
            extra["last_text_to_image_generation"] = {
                "generated_at": datetime.utcnow().isoformat(),
                "style": style_hint_local,
                "style_preset_id": (style_preset_id or "").strip() or None,
                "style_spec": response_meta.get("style_spec"),
                "style_spec_resolution": response_meta.get("style_spec_resolution"),
                "provider": response.provider,
                "model": response.model,
                "count": len(saved_urls),
            }
            env.extra_metadata = extra
            db.commit()
            return saved_urls

        saved = anyio.run(_run)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = (
                f"environment_images:{payload['env_id']}:{len(saved)}"
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


def process_environment_image_variant_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """Celery worker function for environment image-to-image generation."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        env = svc.resolve_environment(db, payload["env_id"])
        if not env:
            raise RuntimeError("environment not found")

        base = payload.get("base_image")
        if not base:
            raise RuntimeError("缺少基准图像")

        backend_base = (
            getattr(settings, "INTERNAL_BACKEND_URL", None)
            or "http://localhost:8000"
        ).rstrip("/")
        image_url = resolve_environment_url(base, backend_base)

        import anyio

        async def _run() -> list[str]:
            model_raw = (payload.get("model") or "").strip() or None
            model_value, provider_from_model = parse_model_and_provider(model_raw)
            prefer_provider = provider_from_model or infer_provider_from_model(
                model_value or ""
            )
            style_hint, style_preset_id, style_spec = sanitize_environment_style(
                payload.get("style"),
                payload.get("style_preset_id"),
                payload.get("style_spec"),
            )
            if (prefer_provider or "").lower() == "openai":
                style_hint_local = normalize_openai_image_style(style_hint)
            else:
                style_hint_local = style_hint
            extra_prompt = payload.get("prompt")
            prompt_value = compose_environment_prompt(
                env,
                extra_prompt
                or "Generate stylistically consistent variants based on this environment reference",
            )
            count_int = int(payload.get("count") or 1)
            size_value = payload.get("size")
            aspect_ratio_value = payload.get("aspect_ratio")

            # Extract reference images and convert to absolute URLs
            reference_images = payload.get("reference_images") or []
            extra_images = normalize_reference_images(reference_images, backend_base)

            aspect_ratio_value = resolve_image_aspect_ratio(
                prefer_provider, model_value, aspect_ratio_value
            )
            response = await ai_service.ai_manager.image_to_image(
                image_url=image_url,
                prompt=prompt_value,
                model=model_value,
                prefer_provider=prefer_provider,
                count=max(1, min(count_int, 4)),
                size=size_value,
                aspect_ratio=aspect_ratio_value,
                style=style_hint_local,
                style_preset_id=style_preset_id,
                style_spec=style_spec,
                extra_images=extra_images,
            )
            if not response.success:
                raise RuntimeError(response.error or "环境图生图生成失败")
            images = (
                response.data.get("images", [])
                if isinstance(response.data, dict)
                else []
            )
            if not images:
                raise RuntimeError("环境图生图接口未返回任何图像")

            saved_urls = await download_and_attach(db, env, images)
            response_meta = getattr(response, "metadata", None)
            if not isinstance(response_meta, dict):
                response_meta = {}
            extra = dict(env.extra_metadata or {})
            extra["last_image_to_image_generation"] = {
                "generated_at": datetime.utcnow().isoformat(),
                "style": style_hint_local,
                "style_preset_id": (style_preset_id or "").strip() or None,
                "style_spec": response_meta.get("style_spec"),
                "style_spec_resolution": response_meta.get("style_spec_resolution"),
                "provider": response.provider,
                "model": response.model,
                "count": len(saved_urls),
            }
            env.extra_metadata = extra
            db.commit()
            return saved_urls

        saved = anyio.run(_run)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = (
                f"environment_image_variants:{payload['env_id']}:{len(saved)}"
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
