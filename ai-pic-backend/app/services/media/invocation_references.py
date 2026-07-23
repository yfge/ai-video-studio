from __future__ import annotations

from typing import Any, Iterable
from urllib.parse import urlsplit

from app.services.media.invocation_assets import persist_image_asset

_REFERENCE_KEYS = (
    "reference_images",
    "reference_image_urls",
    "extra_images",
    "start_reference_images",
    "end_reference_images",
    "character_reference_images",
    "environment_reference_images",
)


def collect_input_references(
    *,
    image_url: str | None = None,
    end_image_url: str | None = None,
    provider_kwargs: dict[str, Any] | None = None,
) -> list[tuple[str, str]]:
    references: list[tuple[str, str]] = []
    _append_reference(references, "start_image", image_url)
    _append_reference(references, "end_image", end_image_url)
    values = provider_kwargs or {}
    for key in _REFERENCE_KEYS:
        raw = values.get(key)
        items = raw if isinstance(raw, list) else [raw]
        for item in items:
            _append_reference(references, key, item)
    return list(dict.fromkeys(references))


async def persist_reference_assets(
    references: Iterable[tuple[str, str]],
    *,
    provider: str,
    model: str | None,
    logger: Any,
) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for role, source in references:
        assets.append(
            await persist_image_asset(
                source,
                role=role,
                provider=provider,
                model=model,
                prefix="ai-invocations/references",
                logger=logger,
            )
        )
    return assets


def safe_media_parameters(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): safe_media_parameters(item)
            for key, item in value.items()
            if key not in {"base64_images", "video_bytes_base64"}
        }
    if isinstance(value, list):
        return [safe_media_parameters(item) for item in value]
    if isinstance(value, str) and value.startswith("data:"):
        return "<inline-media-omitted>"
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        try:
            return urlsplit(value)._replace(query="", fragment="").geturl()
        except Exception:
            return value
    return value


def _append_reference(target: list[tuple[str, str]], role: str, value: Any) -> None:
    candidate = value
    if isinstance(value, dict):
        candidate = value.get("url") or value.get("image_url")
    if isinstance(candidate, str) and candidate.strip():
        target.append((role, candidate.strip()))
