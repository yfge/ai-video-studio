"""
Google image generation module.

Contains text-to-image and image-to-image functionality using Gemini.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

import httpx

from ..base import AIModelType, AIResponse, AITaskType
from ..image_param_utils import normalize_image_params
from .helpers import (
    clean_model_id,
    inline_parts_from_data_urls,
    inline_parts_from_urls,
    normalize_response_modalities,
    parse_images,
)


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

    parts: List[Dict[str, Any]] = []
    if prompt:
        parts.append({"text": prompt})
    base64_images: List[str] = kwargs.pop("base64_images", []) or []
    reference_images_raw = kwargs.pop("reference_images", None)
    if reference_images_raw is None:
        reference_images_raw = kwargs.pop("extra_images", None)
    reference_images: List[str] = []
    if isinstance(reference_images_raw, str):
        reference_images = [reference_images_raw]
    elif isinstance(reference_images_raw, list):
        reference_images = [u for u in reference_images_raw if isinstance(u, str) and u]
    if base64_images:
        parts.extend(inline_parts_from_data_urls(base64_images))
    elif reference_images:
        parts.extend(await inline_parts_from_urls(reference_images, config_timeout))
    body = {"contents": [{"role": "user", "parts": parts}]}

    # Build image config from kwargs
    aspect_ratio = kwargs.get("aspect_ratio") or kwargs.get("aspectRatio")
    image_size = (
        kwargs.get("image_size") or kwargs.get("imageSize") or kwargs.get("size")
    )
    try:
        image_size, aspect_ratio, rules = normalize_image_params(
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
    if image_size and not rules.size_options:
        image_size = None

    image_config: Dict[str, Any] = {}
    if aspect_ratio:
        image_config["aspectRatio"] = aspect_ratio
    if image_size:
        image_config["imageSize"] = image_size

    response_modalities = normalize_response_modalities(
        kwargs.get("response_modalities") or kwargs.get("responseModalities")
    )
    generation_config: Dict[str, Any] = {"responseModalities": response_modalities}
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
        extra_images_raw = kwargs.pop("extra_images", None)
        if extra_images_raw is None:
            extra_images_raw = kwargs.pop("reference_images", None)
        extra_images: List[str] = []
        if isinstance(extra_images_raw, str):
            extra_images = [extra_images_raw]
        elif isinstance(extra_images_raw, list):
            extra_images = [u for u in extra_images_raw if isinstance(u, str) and u]

        parts: List[Dict[str, Any]] = []
        if prompt:
            parts.append({"text": prompt})

        if base64_images:
            parts.extend(inline_parts_from_data_urls(base64_images))
        else:
            urls_raw = [image_url] + extra_images
            urls: List[str] = []
            seen = set()
            for url in urls_raw:
                if not isinstance(url, str) or not url:
                    continue
                if url in seen:
                    continue
                seen.add(url)
                urls.append(url)
            if not urls:
                return AIResponse(
                    success=False,
                    error="缺少参考图像",
                    provider=provider_name,
                    model=model_id,
                    task_type=AITaskType.SCENE_GENERATION,
                    model_type=AIModelType.IMAGE_TO_IMAGE,
                )
            parts.extend(await inline_parts_from_urls(urls, config_timeout))

        body: Dict[str, Any] = {"contents": [{"role": "user", "parts": parts}]}

        aspect_ratio = kwargs.get("aspect_ratio") or kwargs.get("aspectRatio")
        image_size = (
            kwargs.get("image_size") or kwargs.get("imageSize") or kwargs.get("size")
        )
        try:
            image_size, aspect_ratio, rules = normalize_image_params(
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
        if image_size and not rules.size_options:
            image_size = None

        image_config: Dict[str, Any] = {}
        if aspect_ratio:
            image_config["aspectRatio"] = aspect_ratio
        if image_size:
            image_config["imageSize"] = image_size

        response_modalities = normalize_response_modalities(
            kwargs.get("response_modalities") or kwargs.get("responseModalities")
        )
        generation_config: Dict[str, Any] = {"responseModalities": response_modalities}
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
