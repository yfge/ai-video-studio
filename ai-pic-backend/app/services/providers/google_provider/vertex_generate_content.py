"""Vertex AI generateContent helpers.

Gemini API (generativelanguage.googleapis.com) may be geo-restricted. When we
route image generation through Vertex AI, we need a thin wrapper that:
- builds the correct regional endpoint
- attaches Vertex auth headers (OAuth access token / API key)
- maps request/HTTP errors into AIResponse
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

import httpx

from ..base import AIModelType, AIResponse, AITaskType
from .video_vertex import build_vertex_headers


def _vertex_base_url(base_url: str, location: str) -> str:
    base = (base_url or "").rstrip("/")
    if not base or "generativelanguage.googleapis.com" in base:
        return f"https://{location}-aiplatform.googleapis.com"
    return base


def build_vertex_generate_content_url(
    base_url: str,
    *,
    project_id: str,
    location: str,
    model_id: str,
) -> str:
    root = _vertex_base_url(base_url, location)
    return (
        f"{root}/v1/projects/{project_id}/locations/{location}"
        f"/publishers/google/models/{model_id}:generateContent"
    )


def _status_error_message(exc: httpx.HTTPStatusError) -> str:
    text = (exc.response.text or "").strip()
    if text:
        return f"{exc} body={text[:500]}"
    return str(exc)


def error_response(
    *,
    provider_name: str,
    model_id: str,
    task_type: AITaskType,
    model_type: AIModelType,
    message: str,
) -> AIResponse:
    return AIResponse(
        success=False,
        error=message,
        provider=provider_name,
        model=model_id,
        task_type=task_type,
        model_type=model_type,
    )


def vertex_generate_content_endpoint_headers(
    *,
    base_url: str,
    provider_name: str,
    model_id: str,
    vertex_project_id: str,
    vertex_location: str,
    access_token: Optional[str],
    vertex_api_key: Optional[str],
    task_type: AITaskType,
    model_type: AIModelType,
) -> tuple[str, Dict[str, str]] | AIResponse:
    if not vertex_project_id or not vertex_location:
        return error_response(
            provider_name=provider_name,
            model_id=model_id,
            task_type=task_type,
            model_type=model_type,
            message="GoogleProvider 未配置 Vertex project/location",
        )

    headers = build_vertex_headers(access_token, vertex_api_key)
    if not headers:
        return error_response(
            provider_name=provider_name,
            model_id=model_id,
            task_type=task_type,
            model_type=model_type,
            message="GoogleProvider 未配置 Vertex 鉴权（access_token / api_key）",
        )

    endpoint = build_vertex_generate_content_url(
        base_url,
        project_id=vertex_project_id,
        location=vertex_location,
        model_id=model_id,
    )
    return endpoint, headers


async def post_generate_content(
    *,
    client: httpx.AsyncClient,
    endpoint: str,
    headers: Dict[str, str],
    body: Dict[str, Any],
    provider_name: str,
    model_id: str,
    task_type: AITaskType,
    model_type: AIModelType,
    format_error: Callable,
) -> Dict[str, Any] | AIResponse:
    try:
        resp = await client.post(endpoint, json=body, headers=headers)
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, dict):
            return payload
        return error_response(
            provider_name=provider_name,
            model_id=model_id,
            task_type=task_type,
            model_type=model_type,
            message="GoogleProvider Vertex 响应格式异常",
        )
    except httpx.HTTPStatusError as exc:
        return error_response(
            provider_name=provider_name,
            model_id=model_id,
            task_type=task_type,
            model_type=model_type,
            message=_status_error_message(exc),
        )
    except Exception as exc:  # noqa: BLE001
        return error_response(
            provider_name=provider_name,
            model_id=model_id,
            task_type=task_type,
            model_type=model_type,
            message=format_error(exc),
        )
