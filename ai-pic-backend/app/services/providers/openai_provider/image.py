"""
OpenAI image generation module.

Contains GPT Image and DALL-E generation, understanding, and variation functionality.
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any, Callable, Optional

import httpx
from app.core.logging import get_logger
from app.utils.model_utils import (
    DEFAULT_OPENAI_IMAGE_MODEL,
    canonicalize_openai_image_model,
    is_gpt_image_model,
)

from ..base import AIModelType, AIResponse, AITaskType
from ..image_param_utils import normalize_image_params

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


async def generate_image(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    prompt: str,
    model: str = DEFAULT_OPENAI_IMAGE_MODEL,
    size: str = "1024x1024",
    quality: str = "auto",
    style: str = "vivid",
    n: int = 1,
    format_error: Callable = str,
    **kwargs,
) -> AIResponse:
    """Generate images using OpenAI image models."""
    try:
        model = canonicalize_openai_image_model(model) or DEFAULT_OPENAI_IMAGE_MODEL
        try:
            normalized_size, _, _ = normalize_image_params(
                provider_name, model, size, None
            )
        except ValueError as exc:
            return AIResponse(
                success=False,
                error=str(exc),
                provider=provider_name,
                model=model,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )
        size_value = normalized_size or size

        references = kwargs.pop("reference_images", None) or kwargs.pop(
            "extra_images", None
        )
        if is_gpt_image_model(model) and references:
            image_sources = (
                [references] if isinstance(references, str) else list(references)
            )
            image_sources = [str(source) for source in image_sources if source]
            return await _edit_gpt_image(
                client=client,
                base_url=base_url,
                provider_name=provider_name,
                api_key=kwargs.get("api_key"),
                config_timeout=kwargs.get("config_timeout"),
                image_sources=image_sources,
                prompt=prompt,
                model=model,
                size=size_value,
                quality=quality,
                n=n,
                format_error=format_error,
            )

        request_data = _build_generation_request(
            model=model,
            prompt=prompt,
            size=size_value,
            quality=quality,
            style=style,
            n=n,
            output_format=kwargs.get("output_format"),
            output_compression=kwargs.get("output_compression"),
            moderation=kwargs.get("moderation"),
        )

        response = await client.post(
            f"{base_url}/images/generations", json=request_data
        )
        response.raise_for_status()

        data = response.json()
        images = data["data"]
        image_values = _extract_image_values(images)

        return AIResponse(
            success=True,
            data={
                "images": image_values,
                "revised_prompt": (
                    images[0].get("revised_prompt") if model == "dall-e-3" else None
                ),
            },
            provider=provider_name,
            model=model,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
            metadata={
                "size": size_value,
                "quality": quality,
                "style": style if model == "dall-e-3" else None,
                "count": len(image_values),
            },
        )

    except httpx.HTTPStatusError as e:
        detail = None
        try:
            detail = e.response.text
        except Exception:
            detail = None
        msg = format_error(e)
        if detail:
            msg = f"{msg}; body={detail}"
        logger.error(
            "OpenAI generate_image HTTP %s: %s",
            e.response.status_code,
            detail,
            exc_info=True,
        )
        return AIResponse(
            success=False,
            error=msg,
            provider=provider_name,
            model=model,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )
    except Exception as e:
        return AIResponse(
            success=False,
            error=format_error(e),
            provider=provider_name,
            model=model,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )


async def understand_image(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    image_url: str,
    question: str = "请描述这张图片",
    model: str = "gpt-4o",
    max_tokens: Optional[int] = None,
    format_error: Callable = str,
    **kwargs,
) -> AIResponse:
    """Understand image using GPT-4V."""
    try:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ]

        response = await client.post(
            f"{base_url}/chat/completions",
            json={
                "model": model,
                "messages": messages,
                **({} if max_tokens is None else {"max_tokens": max_tokens}),
                **kwargs,
            },
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        return AIResponse(
            success=True,
            data=content,
            provider=provider_name,
            model=model,
            task_type=AITaskType.CHARACTER_CREATION,
            model_type=AIModelType.IMAGE_UNDERSTANDING,
            usage=data.get("usage", {}),
            metadata={"image_url": image_url, "question": question},
        )

    except Exception as e:
        return AIResponse(
            success=False,
            error=format_error(e),
            provider=provider_name,
            model=model,
            task_type=AITaskType.CHARACTER_CREATION,
            model_type=AIModelType.IMAGE_UNDERSTANDING,
        )


async def image_to_image(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    api_key: str,
    config_timeout: Any,
    image_url: str,
    prompt: Optional[str] = None,
    model: str = DEFAULT_OPENAI_IMAGE_MODEL,
    size: str = "1024x1024",
    n: int = 1,
    format_error: Callable = str,
    **kwargs,
) -> AIResponse:
    """Edit with GPT Image models, or create DALL-E 2 variations."""
    model = canonicalize_openai_image_model(model) or DEFAULT_OPENAI_IMAGE_MODEL
    if is_gpt_image_model(model):
        try:
            normalized_size, _, _ = normalize_image_params(
                provider_name, model, size, None
            )
        except ValueError as exc:
            return AIResponse(
                success=False,
                error=str(exc),
                provider=provider_name,
                model=model,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )
        image_sources: list[str] = []
        base64_images: list[str] = kwargs.pop("base64_images", []) or []
        if base64_images:
            image_sources.extend(base64_images)
        elif image_url:
            image_sources.append(image_url)
        extra_images = kwargs.pop("extra_images", []) or kwargs.pop(
            "reference_images", []
        )
        if isinstance(extra_images, list):
            image_sources.extend(str(item) for item in extra_images if item)
        elif extra_images:
            image_sources.append(str(extra_images))

        return await _edit_gpt_image(
            client=client,
            base_url=base_url,
            provider_name=provider_name,
            api_key=api_key,
            config_timeout=config_timeout,
            image_sources=image_sources,
            prompt=prompt or "Edit the provided image.",
            model=model,
            size=normalized_size or size,
            quality=kwargs.get("quality", "auto"),
            n=n,
            format_error=format_error,
            original_image=image_url,
        )

    if model != "dall-e-2":
        return AIResponse(
            success=False,
            error="图像变换仅DALL-E 2支持",
            provider=provider_name,
            model=model,
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
        )

    try:
        # Support data:image;base64 or URL
        image_bytes = None
        content_type = "image/png"
        base64_images: list[str] = kwargs.pop("base64_images", []) or []
        if base64_images and base64_images[0].startswith("data:image"):
            header, b64_data = base64_images[0].split(",", 1)
            content_type = (
                header.split(";")[0].split(":")[1] if ":" in header else "image/png"
            )
            image_bytes = base64.b64decode(b64_data)
        else:
            download_url = image_url
            if isinstance(download_url, str) and download_url.lower().startswith(
                "https://"
            ):
                download_url = "http://" + download_url[len("https://") :]
            image_response = await client.get(download_url)
            image_response.raise_for_status()
            content_type = image_response.headers.get("Content-Type", "image/png")
            image_bytes = image_response.content

        files = {"image": ("image.png", image_bytes, content_type or "image/png")}

        try:
            normalized_size, _, _ = normalize_image_params(
                provider_name, model, size, None
            )
        except ValueError as exc:
            return AIResponse(
                success=False,
                error=str(exc),
                provider=provider_name,
                model=model,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )
        size_value = normalized_size or size

        data = {"n": n, "size": size_value}

        if prompt:
            data["prompt"] = prompt

        # Create new client for multipart request
        form_client = httpx.AsyncClient(
            timeout=config_timeout,
            headers={"Authorization": f"Bearer {api_key}"},
        )

        response = await form_client.post(
            f"{base_url}/images/variations", files=files, data=data
        )
        response.raise_for_status()

        result = response.json()
        images = result["data"]

        await form_client.aclose()

        return AIResponse(
            success=True,
            data={"images": [img["url"] for img in images]},
            provider=provider_name,
            model=model,
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
            metadata={
                "original_image": image_url,
                "size": size_value,
                "count": len(images),
            },
        )

    except Exception as e:
        return AIResponse(
            success=False,
            error=format_error(e),
            provider=provider_name,
            model=model,
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
        )


def _build_generation_request(
    *,
    model: str,
    prompt: str,
    size: str,
    quality: str,
    style: str,
    n: int,
    output_format: str | None,
    output_compression: int | None,
    moderation: str | None,
) -> dict[str, Any]:
    request_n = 1 if model == "dall-e-3" else n
    request_data: dict[str, Any] = {
        "model": model,
        "prompt": _truncate_prompt_for_model(prompt, model),
        "n": request_n,
        "size": size,
    }

    if is_gpt_image_model(model):
        request_data["quality"] = _normalize_gpt_image_quality(quality)
        if output_format in {"png", "jpeg", "webp"}:
            request_data["output_format"] = output_format
        if isinstance(output_compression, int):
            request_data["output_compression"] = output_compression
        if moderation in {"auto", "low"}:
            request_data["moderation"] = moderation
        return request_data

    if model == "dall-e-3":
        request_data.update(
            {
                "quality": _normalize_dalle_quality(quality),
                "style": style if style in {"vivid", "natural"} else "vivid",
            }
        )
    return request_data


async def _edit_gpt_image(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    api_key: str | None,
    config_timeout: Any,
    image_sources: list[str],
    prompt: str,
    model: str,
    size: str,
    quality: str,
    n: int,
    format_error: Callable,
    original_image: str | None = None,
) -> AIResponse:
    if not image_sources:
        return AIResponse(
            success=False,
            error="image_url is required for GPT Image edits",
            provider=provider_name,
            model=model,
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
        )

    try:
        files = await _build_image_edit_files(client, image_sources)
        data: dict[str, Any] = {
            "model": model,
            "prompt": _truncate_prompt_for_model(prompt, model),
            "n": n,
            "size": size,
            "quality": _normalize_gpt_image_quality(quality),
        }

        if api_key:
            async with httpx.AsyncClient(
                timeout=config_timeout,
                headers={"Authorization": f"Bearer {api_key}"},
            ) as form_client:
                response = await form_client.post(
                    f"{base_url}/images/edits", files=files, data=data
                )
        else:
            response = await client.post(
                f"{base_url}/images/edits", files=files, data=data
            )
        response.raise_for_status()
        result = response.json()
        images = result["data"]
        image_values = _extract_image_values(images)

        return AIResponse(
            success=True,
            data={"images": image_values},
            provider=provider_name,
            model=model,
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
            metadata={
                "original_image": original_image or image_sources[0],
                "size": size,
                "quality": quality,
                "count": len(image_values),
            },
        )
    except Exception as e:
        return AIResponse(
            success=False,
            error=format_error(e),
            provider=provider_name,
            model=model,
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
        )


async def _build_image_edit_files(
    client: httpx.AsyncClient,
    image_sources: list[str],
) -> list[tuple[str, tuple[str, bytes, str]]]:
    files: list[tuple[str, tuple[str, bytes, str]]] = []
    for index, source in enumerate(image_sources):
        image_bytes, content_type = await _load_image_bytes(client, source)
        ext = _extension_from_content_type(content_type)
        files.append(
            (
                "image[]",
                (f"image-{index}.{ext}", image_bytes, content_type or "image/png"),
            )
        )
    return files


async def _load_image_bytes(
    client: httpx.AsyncClient,
    source: str,
) -> tuple[bytes, str]:
    if source.startswith("data:image"):
        header, b64_data = source.split(",", 1)
        content_type = (
            header.split(";")[0].split(":")[1] if ":" in header else "image/png"
        )
        return base64.b64decode(b64_data), content_type

    download_url = source
    if isinstance(download_url, str) and download_url.lower().startswith("https://"):
        download_url = "http://" + download_url[len("https://") :]
    image_response = await client.get(download_url)
    image_response.raise_for_status()
    return image_response.content, image_response.headers.get(
        "Content-Type", "image/png"
    )


def _extract_image_values(images: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for img in images:
        if img.get("b64_json"):
            values.append(f"data:image/png;base64,{img['b64_json']}")
        elif img.get("url"):
            values.append(img["url"])
    return values


def _truncate_prompt_for_model(prompt: str, model: str) -> str:
    if is_gpt_image_model(model):
        return prompt[:32000]
    if model == "dall-e-3":
        return prompt[:4000]
    return prompt[:1000]


def _normalize_gpt_image_quality(quality: str | None) -> str:
    value = (quality or "auto").lower()
    if value in {"low", "medium", "high", "auto"}:
        return value
    if value == "hd":
        return "high"
    if value == "standard":
        return "auto"
    return "auto"


def _normalize_dalle_quality(quality: str | None) -> str:
    value = (quality or "standard").lower()
    if value in {"hd", "high"}:
        return "hd"
    return "standard"


def _extension_from_content_type(content_type: str | None) -> str:
    if not content_type or "/" not in content_type:
        return "png"
    return content_type.split("/", 1)[1].split(";", 1)[0] or "png"
