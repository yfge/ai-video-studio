"""
Volcengine image generation module.

Contains text-to-image and image-to-image generation functionality.
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import httpx

from ..base import AIModelType, AIResponse, AITaskType
from ..image_param_utils import normalize_image_params

if TYPE_CHECKING:
    pass


def _normalize_size(size_value: Optional[str]) -> str:
    """Normalize size value to Seedream API format."""
    if not size_value:
        return "1024x1024"
    sv = str(size_value).strip().lower()
    if sv in {"1k", "1024", "1024x1024"}:
        return "1024x1024"
    if sv in {"2k", "2048", "2048x2048"}:
        return "2048x2048"
    if sv in {"4k", "4096", "4096x4096"}:
        return "4096x4096"
    if "x" in sv:
        return sv
    return "1024x1024"


def _build_image_payload(
    image_url: str, backend_base: str
) -> Dict[str, Any]:
    """Build image payload for API request."""
    image_payload: Dict[str, Any] = {}
    url_lower = image_url.lower()

    if url_lower.startswith("data:"):
        # Base64 data URL
        comma_idx = image_url.find(",")
        if comma_idx > 0:
            image_payload["type"] = "base64"
            image_payload["data"] = image_url[comma_idx + 1:]
        else:
            image_payload["type"] = "base64"
            image_payload["data"] = image_url
    elif url_lower.startswith(("http://", "https://")):
        image_payload["type"] = "url"
        image_payload["url"] = image_url
    else:
        # Relative path - convert to absolute URL
        if image_url.startswith("/"):
            image_payload["type"] = "url"
            image_payload["url"] = f"{backend_base}{image_url}"
        else:
            image_payload["type"] = "url"
            image_payload["url"] = f"{backend_base}/{image_url}"

    return image_payload


async def generate_image(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    prompt: str,
    model: Optional[str] = None,
    n: int = 1,
    size: Optional[str] = None,
    style: Optional[str] = None,
    style_preset_id: Optional[str] = None,
    style_spec: Optional[str] = None,
    format_error: callable = str,
    initialize_client: callable = None,
    **kwargs,
) -> AIResponse:
    """Generate images using Seedream API (text-to-image)."""
    ark_model = "seedream-4.5"
    if model:
        normalized = model.strip().lower()
        if normalized.startswith("volcengine-visual"):
            ark_model = "seedream-4.5"
        elif normalized.startswith("seedream"):
            ark_model = model.strip()
        else:
            ark_model = model.strip()

    try:
        size_value, _, _ = normalize_image_params(
            provider_name, ark_model, size, None
        )
    except ValueError as exc:
        return AIResponse(
            success=False,
            error=str(exc),
            provider=provider_name,
            model=ark_model,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )
    effective_size = _normalize_size(size_value)
    count_int = max(1, min(n or 1, 4))

    request_data: Dict[str, Any] = {
        "model": ark_model,
        "prompt": prompt,
        "size": effective_size,
        "n": count_int,
        "response_format": "url",
        "watermark": kwargs.pop("watermark", False),
    }

    if style:
        request_data["style"] = style
    if style_preset_id:
        request_data["style_preset_id"] = style_preset_id
    if style_spec:
        request_data["style_spec"] = style_spec

    # Reference images for style transfer
    ref_images = kwargs.pop("reference_images", None)
    if ref_images and isinstance(ref_images, list):
        request_data["reference_image_data"] = [
            {"url": img} if isinstance(img, str) else img for img in ref_images
        ]

    last_error: Optional[Exception] = None
    for attempt in range(2):
        try:
            response = await client.post(
                f"{base_url}/images/generations",
                json=request_data,
            )
            response.raise_for_status()

            data = response.json()

            if data.get("error"):
                return AIResponse(
                    success=False,
                    error=f"火山引擎文生图错误: {data['error'].get('message', 'Unknown error')}",
                    provider=provider_name,
                    model=ark_model,
                    task_type=AITaskType.SCENE_GENERATION,
                    model_type=AIModelType.TEXT_TO_IMAGE,
                )

            if "data" in data:
                images = data.get("data") or []
                image_urls = [
                    img.get("url")
                    for img in images
                    if isinstance(img, dict) and img.get("url")
                ]
                if image_urls:
                    return AIResponse(
                        success=True,
                        data={"images": image_urls},
                        provider=provider_name,
                        model=ark_model,
                        task_type=AITaskType.SCENE_GENERATION,
                        model_type=AIModelType.TEXT_TO_IMAGE,
                        usage=data.get("usage", {}),
                        metadata={
                            "size": effective_size,
                            "style": style,
                            "style_preset_id": style_preset_id,
                            "style_spec": data.get("style_spec"),
                            "style_spec_resolution": data.get("style_spec_resolution"),
                            "raw_model": ark_model,
                            "count": len(image_urls),
                        },
                    )

            return AIResponse(
                success=False,
                error="火山引擎文生图响应格式错误",
                provider=provider_name,
                model=ark_model,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )

        except Exception as e:
            last_error = e
            if "handler is closed" in str(e).lower() and attempt == 0:
                if initialize_client:
                    await initialize_client()
                continue
            break

    return AIResponse(
        success=False,
        error=format_error(last_error) if last_error else "文生图失败",
        provider=provider_name,
        model=ark_model,
        task_type=AITaskType.SCENE_GENERATION,
        model_type=AIModelType.TEXT_TO_IMAGE,
    )


async def image_to_image(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    image_url: str,
    prompt: str,
    model: Optional[str] = None,
    count: int = 1,
    size: Optional[str] = None,
    style: Optional[str] = None,
    style_preset_id: Optional[str] = None,
    style_spec: Optional[str] = None,
    extra_images: Optional[List[str]] = None,
    backend_base: str = "http://localhost:8000",
    format_error: callable = str,
    initialize_client: callable = None,
    **kwargs,
) -> AIResponse:
    """Generate image variants using Seedream API (image-to-image)."""
    ark_model = "seedream-4.5"
    if model:
        normalized = model.strip().lower()
        if normalized.startswith("volcengine-visual"):
            ark_model = "seedream-4.5"
        elif normalized.startswith("seedream"):
            ark_model = model.strip()
        else:
            ark_model = model.strip()

    try:
        size_value, _, _ = normalize_image_params(
            provider_name, ark_model, size, None
        )
    except ValueError as exc:
        return AIResponse(
            success=False,
            error=str(exc),
            provider=provider_name,
            model=ark_model,
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
        )
    effective_size = _normalize_size(size_value)
    max_images = max(1, min(count or 1, 4))

    # Build image payloads
    image_payloads: List[Dict[str, Any]] = []
    image_payloads.append(_build_image_payload(image_url, backend_base))

    if extra_images:
        for extra in extra_images:
            if isinstance(extra, str) and extra.strip():
                image_payloads.append(_build_image_payload(extra.strip(), backend_base))

    last_error: Optional[Exception] = None
    for attempt in range(2):
        try:
            request_data: Dict[str, Any] = {
                "model": ark_model,
                "prompt": prompt,
                "image": (
                    image_payloads[0]
                    if len(image_payloads) == 1
                    else image_payloads
                ),
                "size": effective_size,
                "response_format": "url",
                "watermark": kwargs.pop("watermark", False),
                # Use non-streaming for image-to-image to simplify upstream processing
                "stream": False,
            }

            if style:
                request_data["style"] = style
            if style_preset_id:
                request_data["style_preset_id"] = style_preset_id
            if style_spec:
                request_data["style_spec"] = style_spec

            # Enable multi-image capability for count > 1
            if max_images > 1:
                request_data["sequential_image_generation"] = "auto"
                request_data["sequential_image_generation_options"] = {
                    "max_images": max_images
                }
            else:
                request_data["sequential_image_generation"] = "disabled"

            response = await client.post(
                f"{base_url}/images/generations",
                json=request_data,
            )
            response.raise_for_status()

            data = response.json()

            if data.get("error"):
                return AIResponse(
                    success=False,
                    error=f"火山引擎图生图错误: {data['error'].get('message', 'Unknown error')}",
                    provider=provider_name,
                    model=model or ark_model,
                    task_type=AITaskType.SCENE_GENERATION,
                    model_type=AIModelType.IMAGE_TO_IMAGE,
                )

            if "data" in data:
                images = data.get("data") or []
                image_urls = [
                    img.get("url")
                    for img in images
                    if isinstance(img, dict) and img.get("url")
                ]
                if image_urls:
                    return AIResponse(
                        success=True,
                        data={"images": image_urls},
                        provider=provider_name,
                        model=model or ark_model,
                        task_type=AITaskType.SCENE_GENERATION,
                        model_type=AIModelType.IMAGE_TO_IMAGE,
                        usage=data.get("usage", {}),
                        metadata={
                            "size": effective_size,
                            "raw_model": ark_model,
                            "count": len(image_urls),
                            "sequential_image_generation": request_data.get(
                                "sequential_image_generation"
                            ),
                        },
                    )

            return AIResponse(
                success=False,
                error="图生图响应格式错误",
                provider=provider_name,
                model=model or ark_model,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )

        except Exception as e:
            last_error = e
            if "handler is closed" in str(e).lower() and attempt == 0:
                if initialize_client:
                    await initialize_client()
                continue
            break

    return AIResponse(
        success=False,
        error=format_error(last_error) if last_error else "图生图失败",
        provider=provider_name,
        model=model or ark_model,
        task_type=AITaskType.SCENE_GENERATION,
        model_type=AIModelType.IMAGE_TO_IMAGE,
    )
