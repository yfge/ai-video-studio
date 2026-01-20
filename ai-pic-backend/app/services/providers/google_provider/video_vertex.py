"""
Google Veo (Vertex AI) helpers.

This module implements Vertex AI-specific request routing, polling and parsing
for Veo video generation. It is intentionally isolated from the Gemini API
code paths so we can keep the public provider surface stable.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from ..polling_utils import TaskPoller, google_operation_status_mapper
from .video_helpers import normalize_operation_path


def parse_vertex_operation_name(operation_name: str) -> Optional[Dict[str, str]]:
    """Parse Vertex AI operation name and extract routing details."""
    if not operation_name:
        return None
    parts = [p for p in str(operation_name).strip("/").split("/") if p]
    try:
        project_index = parts.index("projects")
        location_index = parts.index("locations")
        model_index = parts.index("models")
    except ValueError:
        return None

    if (
        project_index + 1 >= len(parts)
        or location_index + 1 >= len(parts)
        or model_index + 1 >= len(parts)
    ):
        return None

    project_id = parts[project_index + 1]
    location = parts[location_index + 1]
    model_id = parts[model_index + 1]
    if not (project_id and location and model_id):
        return None
    return {"project_id": project_id, "location": location, "model_id": model_id}


def is_vertex_operation_name(operation_name: str) -> bool:
    return parse_vertex_operation_name(operation_name) is not None


def _vertex_base_url(base_url: str, location: str) -> str:
    base = (base_url or "").rstrip("/")
    if not base or "generativelanguage.googleapis.com" in base:
        return f"https://{location}-aiplatform.googleapis.com"
    return base


def build_vertex_predict_long_running_url(
    base_url: str,
    *,
    project_id: str,
    location: str,
    model_id: str,
) -> str:
    root = _vertex_base_url(base_url, location)
    return (
        f"{root}/v1/projects/{project_id}/locations/{location}"
        f"/publishers/google/models/{model_id}:predictLongRunning"
    )


def build_vertex_fetch_predict_operation_url(
    base_url: str,
    *,
    project_id: str,
    location: str,
    model_id: str,
) -> str:
    root = _vertex_base_url(base_url, location)
    return (
        f"{root}/v1/projects/{project_id}/locations/{location}"
        f"/publishers/google/models/{model_id}:fetchPredictOperation"
    )


def build_vertex_headers(
    access_token: Optional[str],
    api_key: Optional[str],
) -> Optional[Dict[str, str]]:
    headers: Dict[str, str] = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    if api_key:
        headers["x-goog-api-key"] = api_key
    return headers or None


async def poll_veo_operation(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    operation_name: str,
    access_token: Optional[str] = None,
    api_key: Optional[str] = None,
    max_attempts: int = 180,
    initial_delay: float = 10.0,
) -> Optional[Dict[str, Any]]:
    """Poll Veo long-running operation via Vertex or Gemini API."""
    vertex = parse_vertex_operation_name(operation_name)

    async def poll_fn() -> Dict[str, Any]:
        if vertex:
            endpoint = build_vertex_fetch_predict_operation_url(
                base_url,
                project_id=vertex["project_id"],
                location=vertex["location"],
                model_id=vertex["model_id"],
            )
            headers = build_vertex_headers(access_token, api_key)
            resp = await client.post(
                endpoint,
                json={"operationName": operation_name},
                headers=headers,
            )
        else:
            op_path = normalize_operation_path(operation_name)
            resp = await client.get(f"{base_url.rstrip('/')}/v1beta/{op_path}")
        resp.raise_for_status()
        return resp.json()

    poller = TaskPoller(
        poll_fn=poll_fn,
        status_mapper=google_operation_status_mapper,
        result_extractor=lambda data: data,
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        task_id=operation_name,
        task_type="video",
    )
    return await poller.poll()


def extract_video_bytes_base64(response: Dict[str, Any]) -> Optional[str]:
    root = response.get("response") or {}
    videos = root.get("videos")
    if isinstance(videos, list) and videos and isinstance(videos[0], dict):
        return videos[0].get("bytesBase64Encoded") or videos[0].get(
            "bytes_base_64_encoded"
        )

    generate = root.get("generateVideoResponse") or root.get("generate_video_response")
    if isinstance(generate, dict):
        candidates = (
            generate.get("generatedSamples")
            or generate.get("generated_samples")
            or generate.get("generatedVideos")
            or generate.get("generated_videos")
            or []
        )
        if (
            isinstance(candidates, list)
            and candidates
            and isinstance(candidates[0], dict)
        ):
            video = candidates[0].get("video")
            if isinstance(video, dict):
                return video.get("bytesBase64Encoded") or video.get(
                    "bytes_base_64_encoded"
                )
    return None


def extract_video_mime_type(response: Dict[str, Any]) -> Optional[str]:
    root = response.get("response") or {}
    videos = root.get("videos")
    if isinstance(videos, list) and videos and isinstance(videos[0], dict):
        return videos[0].get("mimeType") or videos[0].get("mime_type")

    generate = root.get("generateVideoResponse") or root.get("generate_video_response")
    if isinstance(generate, dict):
        candidates = (
            generate.get("generatedSamples")
            or generate.get("generated_samples")
            or generate.get("generatedVideos")
            or generate.get("generated_videos")
            or []
        )
        if (
            isinstance(candidates, list)
            and candidates
            and isinstance(candidates[0], dict)
        ):
            video = candidates[0].get("video")
            if isinstance(video, dict):
                return video.get("mimeType") or video.get("mime_type")
    return None
