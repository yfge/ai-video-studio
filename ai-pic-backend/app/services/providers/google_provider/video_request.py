"""
Google Veo request builder.

Shared between sync and async Veo workflows to keep provider modules small and
consistent across Gemini API and Vertex AI.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .helpers import fetch_image_bytes
from .video_helpers import (
    normalize_ratio,
    normalize_resolution,
    resolve_duration,
    supports_reference_images,
)


async def build_veo_request_body(
    *,
    prompt: Optional[str],
    image_url: Optional[str],
    end_image_url: Optional[str],
    config_timeout: Any,
    model_id: str,
    duration: Optional[int] = None,
    resolution: Optional[str] = None,
    ratio: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    reference_images: Optional[List[Any]] = None,
    person_generation: Optional[str] = None,
    **kwargs: Any,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    instance: Dict[str, Any] = {}
    if prompt:
        instance["prompt"] = prompt
    if image_url:
        instance["image"] = await fetch_image_bytes(image_url, config_timeout)
    if end_image_url:
        instance["lastFrame"] = await fetch_image_bytes(end_image_url, config_timeout)

    body: Dict[str, Any] = {"instances": [instance]}
    parameters: Dict[str, Any] = {}

    resolved_ratio = normalize_ratio(
        ratio
        or kwargs.get("aspectRatio")
        or kwargs.get("aspect_ratio")
        or kwargs.get("ratio")
    )
    if resolved_ratio:
        parameters["aspectRatio"] = resolved_ratio

    resolved_resolution = normalize_resolution(resolution or kwargs.get("resolution"))
    if resolved_resolution:
        parameters["resolution"] = resolved_resolution

    resolved_duration = resolve_duration(
        model_id,
        duration or kwargs.get("durationSeconds"),
        resolution=resolved_resolution,
    )
    if resolved_duration:
        parameters["durationSeconds"] = resolved_duration

    resolved_negative = negative_prompt or kwargs.get("negativePrompt")
    if resolved_negative:
        parameters["negativePrompt"] = resolved_negative

    if person_generation:
        parameters["personGeneration"] = person_generation

    sample_count = kwargs.get("sampleCount") or kwargs.get("sample_count")
    if sample_count is not None:
        try:
            sample_count_int = int(sample_count)
        except (TypeError, ValueError):
            sample_count_int = None
        if sample_count_int in (1, 2, 3, 4):
            parameters["sampleCount"] = sample_count_int

    seed = kwargs.get("seed")
    if seed is not None:
        try:
            seed_int = int(seed)
        except (TypeError, ValueError):
            seed_int = None
        if seed_int is not None and 0 <= seed_int <= 0xFFFFFFFF:
            parameters["seed"] = seed_int

    generate_audio = kwargs.get("generateAudio") or kwargs.get("generate_audio")
    if generate_audio is not None:
        parameters["generateAudio"] = bool(generate_audio)

    if reference_images and supports_reference_images(model_id):
        refs: List[Dict[str, Any]] = []
        for item in reference_images[:3]:
            if isinstance(item, str):
                image_payload = await fetch_image_bytes(item, config_timeout)
                refs.append({"image": image_payload, "referenceType": "asset"})
            elif isinstance(item, dict):
                image_value = item.get("image") or item.get("image_url") or item.get("url")
                if not image_value:
                    continue
                image_payload = await fetch_image_bytes(image_value, config_timeout)
                reference_type = (
                    item.get("reference_type") or item.get("referenceType") or "asset"
                )
                refs.append({"image": image_payload, "referenceType": reference_type})
        if refs:
            parameters["referenceImages"] = refs

    if parameters:
        body["parameters"] = parameters

    resolved: Dict[str, Any] = {
        "aspect_ratio": resolved_ratio,
        "resolution": resolved_resolution,
        "duration": resolved_duration,
    }
    return body, resolved

