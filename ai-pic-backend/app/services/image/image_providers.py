"""
Image generation provider implementations.

Provides direct API integrations for image generation providers:
- OpenAI DALL-E
- Keling AI
- Stability AI
"""

from typing import Any, Optional

import httpx
from app.core.config import settings
from app.core.logging import get_logger
from app.services.image.image_persistence import save_base64_image

logger = get_logger()


async def generate_with_keling(
    ai_manager,
    prompt: str,
    style: str,
    category: str,
    model: str = "kling-v2-1",
    *,
    style_preset_id: str | None = None,
    style_spec: Any | None = None,
    aspect_ratio: str | None = None,
) -> Optional[str]:
    """
    Generate image using Keling AI.

    Args:
        ai_manager: AI service manager instance.
        prompt: Generation prompt.
        style: Image style.
        category: Image category.
        model: Keling model to use.
        style_preset_id: Optional style preset.
        style_spec: Optional style specification.
        aspect_ratio: Optional aspect ratio.

    Returns:
        Generated image URL or None on failure.
    """
    if not ai_manager:
        logger.warning("AI manager not initialized, cannot use Keling AI")
        return None

    try:
        logger.info(f"Generating image with Keling AI: {model}")

        response = await ai_manager.generate_image(
            prompt=prompt,
            width=1024,
            height=1024,
            style=style,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
            model=model,
            prefer_provider="keling",
            aspect_ratio=aspect_ratio,
        )

        if response.success:
            images = response.data.get("images", [])
            if images:
                image_url = images[0]
                logger.info(
                    f"Keling AI image generation success: {image_url[:100] if isinstance(image_url, str) else str(image_url)[:100]}..."
                )
                return image_url
            else:
                logger.error("Keling AI returned empty image list")
                return None
        else:
            logger.error(f"Keling AI image generation failed: {response.error}")
            return None

    except Exception as e:
        logger.error(f"Keling AI image generation error: {e}")
        return None


async def generate_with_openai_dalle(
    prompt: str,
    style: str,
    category: str,
    size: str | None = None,
    openai_api_key: str | None = None,
) -> Optional[str]:
    """
    Generate image using OpenAI DALL-E.

    Args:
        prompt: Generation prompt (max 1000 chars).
        style: Image style ('vivid' or 'natural').
        category: Image category (for logging).
        size: Image size (e.g., '1024x1024').
        openai_api_key: Optional API key override.

    Returns:
        Generated image as base64 data URI or URL, or None on failure.
    """
    api_key = openai_api_key or settings.OPENAI_API_KEY
    if not api_key:
        return None

    base_url = settings.OPENAI_BASE_URL or "https://api.openai.com/v1"

    # Normalize style for OpenAI
    openai_style = (
        style
        if style in {"vivid", "natural"}
        else ("natural" if style == "realistic" else "vivid")
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "dall-e-3",
                    "prompt": prompt[:1000],  # DALL-E 3 prompt limit
                    "n": 1,
                    "size": size or "1024x1024",
                    "quality": "hd",
                    "style": openai_style,
                    "response_format": "b64_json",  # Avoid URL expiration
                },
                timeout=60.0,
            )
            response.raise_for_status()
            result = response.json()

            # Handle base64 response
            if "b64_json" in result["data"][0]:
                base64_data = result["data"][0]["b64_json"]
                logger.info(f"Received OpenAI base64 image, length: {len(base64_data)}")
                return f"data:image/png;base64,{base64_data}"
            else:
                # Fallback to URL format
                image_url = result["data"][0]["url"]
                logger.info(f"Received OpenAI image URL: {image_url[:100]}...")
                return image_url

    except Exception as e:
        logger.error(f"OpenAI DALL-E generation failed: {e}")
        if hasattr(e, "response"):
            try:
                error_detail = e.response.json()
                logger.error(f"OpenAI API error details: {error_detail}")
            except Exception:
                logger.error(f"OpenAI API response: {e.response.text}")
        return None


async def generate_with_stability(
    prompt: str,
    style: str,
    category: str,
    stability_api_key: str | None = None,
) -> Optional[str]:
    """
    Generate image using Stability AI.

    Args:
        prompt: Generation prompt.
        style: Image style.
        category: Image category.
        stability_api_key: Optional API key override.

    Returns:
        Path to saved image or None on failure.
    """
    api_key = stability_api_key or settings.STABILITY_API_KEY
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "text_prompts": [{"text": prompt, "weight": 1}],
                    "cfg_scale": 7,
                    "height": 1024,
                    "width": 1024,
                    "samples": 1,
                    "steps": 30,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            result = response.json()

            # Stability AI returns base64-encoded image
            image_data = result["artifacts"][0]["base64"]
            return await save_base64_image(image_data, "stability")

    except Exception as e:
        logger.error(f"Stability AI generation failed: {e}")
        return None


async def generate_with_custom_service(
    prompt: str,
    style: str,
    category: str,
    base_url: str | None = None,
    api_key: str | None = None,
) -> Optional[str]:
    """
    Generate image using custom AI service.

    Args:
        prompt: Generation prompt.
        style: Image style.
        category: Image category.
        base_url: Custom service base URL.
        api_key: Custom service API key.

    Returns:
        Generated image URL or None on failure.
    """
    service_url = base_url or settings.AI_SERVICE_URL
    service_key = api_key or settings.AI_API_KEY

    if not service_url or not service_key:
        return None

    payload = {
        "prompt": prompt,
        "parameters": {
            "style": style,
            "category": category,
            "width": 1024,
            "height": 1024,
            "quality": "high",
        },
    }

    headers = {
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{service_url}/generate",
                json=payload,
                headers=headers,
                timeout=60.0,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("image_url")

    except Exception as e:
        logger.error(f"Custom AI service generation failed: {e}")
        return None
