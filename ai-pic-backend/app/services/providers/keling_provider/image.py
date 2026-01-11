"""
Keling image generation module.

Contains text-to-image generation functionality with polling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

import httpx

from ..base import AIModelType, AIResponse, AITaskType
from ..image_param_utils import normalize_image_params, normalize_keling_resolution
from ..polling_utils import TaskPoller, keling_status_mapper

if TYPE_CHECKING:
    pass


_KELING_IMAGE_MODEL_ALIASES = {
    "kling-image-v1": "kling-v1",
    "kling-image-v2": "kling-v2-1",
    "kling-image": "kling-v1",
}


def normalize_keling_image_model(model: str | None) -> str:
    raw = (model or "").strip()
    if not raw:
        return "kling-v2-1"
    mapped = _KELING_IMAGE_MODEL_ALIASES.get(raw.lower())
    return mapped or raw


async def poll_image_task(
    client: httpx.AsyncClient,
    base_url: str,
    task_id: str,
    get_auth_headers: Callable[[], Dict[str, str]],
) -> Optional[Dict[str, Any]]:
    """
    Poll image generation task status.

    Endpoint: GET /v1/images/generations/{task_id}
    """

    async def poll_fn() -> Dict[str, Any]:
        response = await client.get(
            f"{base_url}/v1/images/generations/{task_id}",
            headers=get_auth_headers(),
        )
        response.raise_for_status()
        return response.json().get("data", {})

    def extract_result(data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract images from response"""
        task_result = data.get("task_result", {})
        images = task_result.get("images", [])
        return {"images": images}

    poller = TaskPoller(
        poll_fn=poll_fn,
        status_mapper=keling_status_mapper,
        result_extractor=extract_result,
        max_attempts=60,  # 5 minutes with 5s interval
        initial_delay=5.0,
        task_id=task_id,
        task_type="image",
    )

    return await poller.poll()


async def generate_image(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    get_auth_headers: Callable[[], Dict[str, str]],
    prompt: str,
    model: str = "kling-v2-1",
    negative_prompt: Optional[str] = None,
    image: Optional[str] = None,
    image_reference: Optional[str] = None,
    image_fidelity: Optional[float] = None,
    human_fidelity: Optional[float] = None,
    resolution: str = "1k",
    n: int = 1,
    aspect_ratio: Optional[str] = None,
    format_error: Callable = str,
    **kwargs,
) -> AIResponse:
    """
    Generate images using Keling AI.

    Endpoint: POST /v1/images/generations
    Polling: GET /v1/images/generations/{task_id}

    Args:
        client: HTTP client
        base_url: API base URL
        provider_name: Provider name for response
        get_auth_headers: Function to get fresh auth headers
        prompt: Text prompt for image generation
        model: Model name (e.g. kling-v1 / kling-v2-1)
        negative_prompt: Negative prompt to avoid certain elements
        image: Reference image (URL or base64 data URL)
        image_reference: Reference mode ("character" or "face")
        image_fidelity: Image similarity (0.5-1.0)
        human_fidelity: Human feature fidelity (0.5-1.0)
        resolution: Output resolution ("1k" or "2k")
        n: Number of images to generate (1-4)
        aspect_ratio: Aspect ratio like "16:9", "1:1", etc.

    Returns:
        AIResponse with generated images
    """
    model_name = normalize_keling_image_model(model)
    try:
        size_value = kwargs.get("size") or resolution
        try:
            normalized_size, aspect_ratio, _ = normalize_image_params(
                provider_name, model_name, size_value, aspect_ratio
            )
        except ValueError as exc:
            return AIResponse(
                success=False,
                error=str(exc),
                provider=provider_name,
                model=model_name,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )
        resolution_value = normalize_keling_resolution(normalized_size) or resolution

        # Build request payload according to API spec
        request_data = {
            "model_name": model_name,
            "prompt": prompt,
            "n": n,
            "resolution": resolution_value,
        }

        # Add optional parameters
        if negative_prompt:
            request_data["negative_prompt"] = negative_prompt
        if image:
            payload_image = image
            lower_image = payload_image.lower()
            if lower_image.startswith("data:") and "base64," in lower_image:
                payload_image = payload_image.split(",", 1)[1].strip()
            request_data["image"] = payload_image
        if image_reference:
            request_data["image_reference"] = image_reference
        if image_fidelity is not None:
            request_data["image_fidelity"] = image_fidelity
        if human_fidelity is not None:
            request_data["human_fidelity"] = human_fidelity
        if aspect_ratio:
            request_data["aspect_ratio"] = aspect_ratio

        # Create image generation task
        try:
            response = await client.post(
                f"{base_url}/v1/images/generations",
                json=request_data,
                headers=get_auth_headers(),
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail: str = ""
            try:
                payload = exc.response.json()
                code = payload.get("code")
                msg = (
                    payload.get("message") or payload.get("msg") or payload.get("error")
                )
                request_id = payload.get("request_id") or payload.get("requestId")
                detail = f"code={code}, message={msg}, request_id={request_id}"
            except Exception:
                detail = exc.response.text or str(exc)
            return AIResponse(
                success=False,
                error=f"Keling image generation HTTP {exc.response.status_code}: {detail}",
                provider=provider_name,
                model=model_name,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )
        data = response.json()

        task_id = data.get("data", {}).get("task_id")
        if not task_id:
            return AIResponse(
                success=False,
                error="No task_id in response",
                provider=provider_name,
                model=model_name,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )

        # Poll task status
        result = await poll_image_task(client, base_url, task_id, get_auth_headers)

        if result and "images" in result:
            return AIResponse(
                success=True,
                data={"images": result["images"]},
                provider=provider_name,
                model=model_name,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
                metadata={
                    "task_id": task_id,
                    "resolution": resolution_value,
                    "aspect_ratio": aspect_ratio,
                    "prompt": prompt,
                    "n": n,
                },
            )
        else:
            return AIResponse(
                success=False,
                error="Image generation task failed or timed out",
                provider=provider_name,
                model=model_name,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )

    except Exception as e:
        return AIResponse(
            success=False,
            error=format_error(e),
            provider=provider_name,
            model=model_name,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )


async def image_to_image(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    get_auth_headers: Callable[[], Dict[str, str]],
    image_url: str,
    prompt: Optional[str] = None,
    model: str = "kling-v2-1",
    negative_prompt: Optional[str] = None,
    resolution: str = "1k",
    n: int = 1,
    aspect_ratio: Optional[str] = None,
    base64_images: Optional[list[str]] = None,
    image_reference: Optional[str] = None,
    image_fidelity: Optional[float] = None,
    human_fidelity: Optional[float] = None,
    format_error: Callable = str,
    **kwargs,
) -> AIResponse:
    """Generate image variants using Keling AI (image-to-image)."""
    reference_image = None
    if base64_images:
        reference_image = base64_images[0]
    elif image_url:
        reference_image = image_url

    response = await generate_image(
        client=client,
        base_url=base_url,
        provider_name=provider_name,
        get_auth_headers=get_auth_headers,
        prompt=prompt or "",
        model=model,
        negative_prompt=negative_prompt,
        image=reference_image,
        image_reference=image_reference,
        image_fidelity=image_fidelity,
        human_fidelity=human_fidelity,
        resolution=resolution,
        n=n,
        aspect_ratio=aspect_ratio,
        format_error=format_error,
        **kwargs,
    )
    response.task_type = AITaskType.SCENE_GENERATION
    response.model_type = AIModelType.IMAGE_TO_IMAGE
    if response.metadata is not None and isinstance(response.metadata, dict):
        response.metadata.setdefault("init_image", image_url)
        response.metadata.setdefault(
            "reference_mode", "base64" if base64_images else "url"
        )
        if base64_images is not None:
            response.metadata.setdefault("reference_images_count", len(base64_images))
    elif response.metadata is None:
        response.metadata = {
            "init_image": image_url,
            "reference_mode": "base64" if base64_images else "url",
            "reference_images_count": len(base64_images or []),
        }
    return response
