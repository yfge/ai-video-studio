"""
OpenAI image generation module.

Contains DALL-E image generation, understanding, and variation functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

import httpx

from app.core.logging import get_logger

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
    model: str = "dall-e-3",
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid",
    n: int = 1,
    format_error: Callable = str,
    **kwargs,
) -> AIResponse:
    """Generate images using DALL-E."""
    try:
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

        # DALL-E 3 parameters
        request_data = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size_value,
        }

        # DALL-E 3 specific parameters
        if model == "dall-e-3":
            request_data.update({"quality": quality, "style": style})

        response = await client.post(
            f"{base_url}/images/generations", json=request_data
        )
        response.raise_for_status()

        data = response.json()
        images = data["data"]

        return AIResponse(
            success=True,
            data={
                "images": [img["url"] for img in images],
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
                "style": style,
                "count": len(images),
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
    model: str = "dall-e-2",
    size: str = "1024x1024",
    n: int = 1,
    format_error: Callable = str,
    **kwargs,
) -> AIResponse:
    """DALL-E image variation (DALL-E 2 only)."""
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
            import base64

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
