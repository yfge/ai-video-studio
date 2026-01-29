"""Google image generation via Vertex AI (generateContent).

Gemini API (generativelanguage.googleapis.com) can be geo-restricted. Vertex AI
endpoints are often usable in environments where Gemini API is blocked.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

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
from .vertex_generate_content import (
    error_response,
    post_generate_content,
    vertex_generate_content_endpoint_headers,
)

DEFAULT_MODEL = "gemini-2.5-flash-image"


def _build_generate_content_body(
    *,
    provider_name: str,
    model_id: str,
    parts: List[Dict[str, Any]],
    task_type: AITaskType,
    model_type: AIModelType,
    **kwargs: Any,
) -> tuple[Dict[str, Any], Optional[str]] | AIResponse:
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
        return error_response(
            provider_name=provider_name,
            model_id=model_id,
            task_type=task_type,
            model_type=model_type,
            message=str(exc),
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
    return body, aspect_ratio


async def generate_image(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    config_timeout: Any,
    prompt: str,
    *,
    vertex_project_id: str,
    vertex_location: str,
    access_token: Optional[str],
    vertex_api_key: Optional[str],
    model: str = None,
    format_error: Callable = str,
    **kwargs: Any,
) -> AIResponse:
    """Generate images using Vertex AI Gemini (text-to-image)."""
    model_id = clean_model_id(model) or DEFAULT_MODEL
    ctx = vertex_generate_content_endpoint_headers(
        base_url=base_url,
        provider_name=provider_name,
        model_id=model_id,
        vertex_project_id=vertex_project_id,
        vertex_location=vertex_location,
        access_token=access_token,
        vertex_api_key=vertex_api_key,
        task_type=AITaskType.PORTRAIT_GENERATION,
        model_type=AIModelType.TEXT_TO_IMAGE,
    )
    if isinstance(ctx, AIResponse):
        return ctx
    endpoint, headers = ctx

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

    body_or_error = _build_generate_content_body(
        provider_name=provider_name,
        model_id=model_id,
        parts=parts,
        task_type=AITaskType.PORTRAIT_GENERATION,
        model_type=AIModelType.TEXT_TO_IMAGE,
        **kwargs,
    )
    if isinstance(body_or_error, AIResponse):
        return body_or_error
    body, aspect_ratio = body_or_error

    meta: Dict[str, Any] = {"vertex": True}
    if aspect_ratio:
        meta["aspect_ratio"] = aspect_ratio
    payload = await post_generate_content(
        client=client,
        endpoint=endpoint,
        headers=headers,
        body=body,
        provider_name=provider_name,
        model_id=model_id,
        task_type=AITaskType.PORTRAIT_GENERATION,
        model_type=AIModelType.TEXT_TO_IMAGE,
        format_error=format_error,
    )
    if isinstance(payload, AIResponse):
        return payload
    images = parse_images(payload)
    if not images:
        return error_response(
            provider_name=provider_name,
            model_id=model_id,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
            message="GoogleProvider 图像生成响应为空",
        )
    return AIResponse(
        success=True,
        data={"images": images},
        provider=provider_name,
        model=model_id,
        task_type=AITaskType.PORTRAIT_GENERATION,
        model_type=AIModelType.TEXT_TO_IMAGE,
        metadata=meta,
    )


async def image_to_image(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    config_timeout: Any,
    image_url: str,
    *,
    vertex_project_id: str,
    vertex_location: str,
    access_token: Optional[str],
    vertex_api_key: Optional[str],
    prompt: str = None,
    model: str = None,
    format_error: Callable = str,
    **kwargs: Any,
) -> AIResponse:
    """Generate images using Vertex AI Gemini (image-to-image with reference)."""
    model_id = clean_model_id(model) or DEFAULT_MODEL
    ctx = vertex_generate_content_endpoint_headers(
        base_url=base_url,
        provider_name=provider_name,
        model_id=model_id,
        vertex_project_id=vertex_project_id,
        vertex_location=vertex_location,
        access_token=access_token,
        vertex_api_key=vertex_api_key,
        task_type=AITaskType.SCENE_GENERATION,
        model_type=AIModelType.IMAGE_TO_IMAGE,
    )
    if isinstance(ctx, AIResponse):
        return ctx
    endpoint, headers = ctx

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
            if not isinstance(url, str) or not url or url in seen:
                continue
            seen.add(url)
            urls.append(url)
        if not urls:
            return error_response(
                provider_name=provider_name,
                model_id=model_id,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
                message="缺少参考图像",
            )
        parts.extend(await inline_parts_from_urls(urls, config_timeout))

    body_or_error = _build_generate_content_body(
        provider_name=provider_name,
        model_id=model_id,
        parts=parts,
        task_type=AITaskType.SCENE_GENERATION,
        model_type=AIModelType.IMAGE_TO_IMAGE,
        **kwargs,
    )
    if isinstance(body_or_error, AIResponse):
        return body_or_error
    body, aspect_ratio = body_or_error

    meta: Dict[str, Any] = {"reference_image": image_url, "vertex": True}
    if aspect_ratio:
        meta["aspect_ratio"] = aspect_ratio
    payload = await post_generate_content(
        client=client,
        endpoint=endpoint,
        headers=headers,
        body=body,
        provider_name=provider_name,
        model_id=model_id,
        task_type=AITaskType.SCENE_GENERATION,
        model_type=AIModelType.IMAGE_TO_IMAGE,
        format_error=format_error,
    )
    if isinstance(payload, AIResponse):
        return payload
    images = parse_images(payload)
    if not images:
        return error_response(
            provider_name=provider_name,
            model_id=model_id,
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
            message="GoogleProvider 图像生成响应为空",
        )
    return AIResponse(
        success=True,
        data={"images": images},
        provider=provider_name,
        model=model_id,
        task_type=AITaskType.SCENE_GENERATION,
        model_type=AIModelType.IMAGE_TO_IMAGE,
        metadata=meta,
    )
