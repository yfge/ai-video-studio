"""Google image routing helpers.

Prefer Vertex AI when configured (bypasses Gemini API geo restrictions), while
keeping a Gemini API fallback when an API key is available.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

import httpx

from ..base import AIResponse
from . import image as image_module
from . import image_vertex as image_vertex_module


def _can_use_vertex(
    *,
    vertex_project_id: Optional[str],
    vertex_location: Optional[str],
    access_token: Optional[str],
    vertex_api_key: Optional[str],
) -> bool:
    return bool(
        vertex_project_id and vertex_location and (access_token or vertex_api_key)
    )


async def generate_image(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    api_key: Optional[str],
    config_timeout: Any,
    prompt: str,
    model: str | None,
    vertex_project_id: Optional[str],
    vertex_location: Optional[str],
    access_token: Optional[str],
    vertex_api_key: Optional[str],
    format_error: Callable,
    **kwargs: Any,
) -> AIResponse:
    if _can_use_vertex(
        vertex_project_id=vertex_project_id,
        vertex_location=vertex_location,
        access_token=access_token,
        vertex_api_key=vertex_api_key,
    ):
        assert vertex_project_id and vertex_location
        vertex_resp = await image_vertex_module.generate_image(
            client=client,
            base_url=base_url,
            provider_name=provider_name,
            config_timeout=config_timeout,
            prompt=prompt,
            vertex_project_id=vertex_project_id,
            vertex_location=vertex_location,
            access_token=access_token,
            vertex_api_key=vertex_api_key,
            model=model,
            format_error=format_error,
            **kwargs,
        )
        if vertex_resp.success or not api_key:
            return vertex_resp

        gemini_resp = await image_module.generate_image(
            client=client,
            base_url=base_url,
            provider_name=provider_name,
            api_key=api_key,
            config_timeout=config_timeout,
            prompt=prompt,
            model=model,
            format_error=format_error,
            **kwargs,
        )
        if gemini_resp.success:
            return gemini_resp
        if vertex_resp.error and gemini_resp.error:
            vertex_resp.error = (
                f"{vertex_resp.error} | Gemini fallback: {gemini_resp.error}"
            )
        return vertex_resp

    return await image_module.generate_image(
        client=client,
        base_url=base_url,
        provider_name=provider_name,
        api_key=api_key,
        config_timeout=config_timeout,
        prompt=prompt,
        model=model,
        format_error=format_error,
        **kwargs,
    )


async def image_to_image(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    api_key: Optional[str],
    config_timeout: Any,
    image_url: str,
    prompt: str | None,
    model: str | None,
    vertex_project_id: Optional[str],
    vertex_location: Optional[str],
    access_token: Optional[str],
    vertex_api_key: Optional[str],
    format_error: Callable,
    **kwargs: Any,
) -> AIResponse:
    if _can_use_vertex(
        vertex_project_id=vertex_project_id,
        vertex_location=vertex_location,
        access_token=access_token,
        vertex_api_key=vertex_api_key,
    ):
        assert vertex_project_id and vertex_location
        vertex_resp = await image_vertex_module.image_to_image(
            client=client,
            base_url=base_url,
            provider_name=provider_name,
            config_timeout=config_timeout,
            image_url=image_url,
            prompt=prompt,
            vertex_project_id=vertex_project_id,
            vertex_location=vertex_location,
            access_token=access_token,
            vertex_api_key=vertex_api_key,
            model=model,
            format_error=format_error,
            **kwargs,
        )
        if vertex_resp.success or not api_key:
            return vertex_resp

        gemini_resp = await image_module.image_to_image(
            client=client,
            base_url=base_url,
            provider_name=provider_name,
            api_key=api_key,
            config_timeout=config_timeout,
            image_url=image_url,
            prompt=prompt,
            model=model,
            format_error=format_error,
            **kwargs,
        )
        if gemini_resp.success:
            return gemini_resp
        if vertex_resp.error and gemini_resp.error:
            vertex_resp.error = (
                f"{vertex_resp.error} | Gemini fallback: {gemini_resp.error}"
            )
        return vertex_resp

    return await image_module.image_to_image(
        client=client,
        base_url=base_url,
        provider_name=provider_name,
        api_key=api_key,
        config_timeout=config_timeout,
        image_url=image_url,
        prompt=prompt,
        model=model,
        format_error=format_error,
        **kwargs,
    )
