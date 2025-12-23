"""
Google image generation module.

Contains text-to-image and image-to-image functionality using Gemini.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import httpx

from ..base import AIModelType, AIResponse, AITaskType
from ..image_param_utils import normalize_image_params
from .helpers import clean_model_id, fetch_inline_image, parse_images


async def generate_image(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    api_key: str,
    config_timeout: Any,
    prompt: str,
    model: str = None,
    format_error: Callable = str,
    **kwargs: Any,
) -> AIResponse:
    """Generate images using Gemini (text-to-image)."""
    default_model = "gemini-2.5-flash-image"

    if not api_key:
        return AIResponse(
            success=False,
            error="GoogleProvider 未配置 API Key",
            provider=provider_name,
            model=model or default_model,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )

    # Clean model ID, remove possible provider prefix
    model_id = clean_model_id(model) or default_model
    endpoint = f"{base_url.rstrip('/')}/v1beta/models/{model_id}:generateContent"

    if client is None:
        return AIResponse(
            success=False,
            error="Google 客户端未初始化",
            provider=provider_name,
            model=model_id,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )

    body = {
        "model": model_id,
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    }

    # Build image config from kwargs
    aspect_ratio = kwargs.get("aspect_ratio")
    image_size = kwargs.get("image_size") or kwargs.get("size")
    try:
        image_size, aspect_ratio, _ = normalize_image_params(
            provider_name, model_id, image_size, aspect_ratio
        )
    except ValueError as exc:
        return AIResponse(
            success=False,
            error=str(exc),
            provider=provider_name,
            model=model_id,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )
    image_config: Dict[str, Any] = {}
    if aspect_ratio:
        image_config["aspectRatio"] = aspect_ratio
    if image_size:
        image_config["imageSize"] = image_size

    generation_config: Dict[str, Any] = {
        "responseModalities": ["TEXT", "IMAGE"]
    }
    if image_config:
        generation_config["imageConfig"] = image_config
    body["generationConfig"] = generation_config

    try:
        resp = await client.post(endpoint, json=body)
        resp.raise_for_status()
        payload = resp.json()
        images = parse_images(payload)
        if not images:
            return AIResponse(
                success=False,
                error="GoogleProvider 图像生成响应为空",
                provider=provider_name,
                model=model_id,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )
        return AIResponse(
            success=True,
            data={"images": images},
            provider=provider_name,
            model=model_id,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
            metadata={"aspect_ratio": aspect_ratio},
        )
    except Exception as exc:
        return AIResponse(
            success=False,
            error=format_error(exc),
            provider=provider_name,
            model=model_id,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )


async def image_to_image(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    api_key: str,
    config_timeout: Any,
    image_url: str,
    prompt: str = None,
    model: str = None,
    format_error: Callable = str,
    **kwargs: Any,
) -> AIResponse:
    """Generate images using Gemini (image-to-image with reference)."""
    default_model = "gemini-2.5-flash-image"

    if not api_key:
        return AIResponse(
            success=False,
            error="GoogleProvider 未配置 API Key",
            provider=provider_name,
            model=model or default_model,
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
        )

    # Clean model ID, remove possible provider prefix
    model_id = clean_model_id(model) or default_model
    endpoint = f"{base_url.rstrip('/')}/v1beta/models/{model_id}:generateContent"

    if client is None:
        return AIResponse(
            success=False,
            error="Google 客户端未初始化",
            provider=provider_name,
            model=model_id,
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
        )

    try:
        # Prefer preloaded base64_images (data:image/...;base64,...),
        # to support multiple reference images and avoid redundant downloads.
        base64_images: List[str] = kwargs.pop("base64_images", []) or []
        parts: List[Dict[str, Any]] = []
        if prompt:
            parts.append({"text": prompt})

        if base64_images:
            # Support up to 14 reference images
            for data_url in base64_images[:14]:
                if not isinstance(data_url, str) or not data_url:
                    continue
                mime_type = "image/png"
                b64_data = data_url
                if data_url.startswith("data:"):
                    # Format: data:image/png;base64,AAAA...
                    try:
                        header, b64_data = data_url.split(",", 1)
                        header = header[5:]  # Remove "data:"
                        if ";" in header:
                            mime_type = header.split(";", 1)[0] or "image/png"
                        elif header:
                            mime_type = header
                    except ValueError:
                        # Fall back to original string
                        b64_data = data_url
                parts.append(
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": b64_data,
                        }
                    }
                )
        else:
            # Fallback: download from URL if not preloaded
            inline_image = await fetch_inline_image(image_url, config_timeout)
            parts.append({"inlineData": inline_image})

        body: Dict[str, Any] = {
            "model": model_id,
            "contents": [{"role": "user", "parts": parts}],
        }

        aspect_ratio = kwargs.get("aspect_ratio")
        image_size = kwargs.get("image_size") or kwargs.get("size")
        try:
            image_size, aspect_ratio, _ = normalize_image_params(
                provider_name, model_id, image_size, aspect_ratio
            )
        except ValueError as exc:
            return AIResponse(
                success=False,
                error=str(exc),
                provider=provider_name,
                model=model_id,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )
        image_config: Dict[str, Any] = {}
        if aspect_ratio:
            image_config["aspectRatio"] = aspect_ratio
        if image_size:
            image_config["imageSize"] = image_size

        generation_config: Dict[str, Any] = {
            "responseModalities": ["TEXT", "IMAGE"]
        }
        if image_config:
            generation_config["imageConfig"] = image_config
        body["generationConfig"] = generation_config

        resp = await client.post(endpoint, json=body)
        resp.raise_for_status()
        payload = resp.json()
        images = parse_images(payload)
        if not images:
            return AIResponse(
                success=False,
                error="GoogleProvider 图生图响应为空",
                provider=provider_name,
                model=model_id,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )
        return AIResponse(
            success=True,
            data={"images": images},
            provider=provider_name,
            model=model_id,
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
            metadata={"reference_image": image_url},
        )
    except Exception as exc:
        return AIResponse(
            success=False,
            error=format_error(exc),
            provider=provider_name,
            model=model_id,
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
        )
