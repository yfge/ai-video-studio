from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from app.services.media.media_persistence import (
    build_generation_metadata,
    upload_base64,
    upload_from_url,
)

INVOCATION_ID_KEY = "llm_invocation_id"


@dataclass(frozen=True)
class ImagePersistenceResult:
    urls: list[str]
    assets: list[dict[str, Any]]

    @property
    def fully_persisted(self) -> bool:
        return bool(self.assets) and all(
            bool(asset.get("persisted")) for asset in self.assets
        )


async def persist_generated_images(
    images: Any,
    *,
    provider: str,
    model: str | None,
    prefix: str,
    logger: Any,
) -> ImagePersistenceResult:
    urls: list[str] = []
    assets: list[dict[str, Any]] = []
    for index, source in enumerate(_normalize_values(images)):
        asset = await persist_image_asset(
            source,
            role=f"image_{index}",
            provider=provider,
            model=model,
            prefix=prefix,
            logger=logger,
        )
        assets.append(asset)
        urls.append(str(asset.get("url") or source))
    return ImagePersistenceResult(urls=urls, assets=assets)


def image_audit_response(
    response_data: Any, result: ImagePersistenceResult
) -> dict[str, Any]:
    payload = dict(response_data) if isinstance(response_data, dict) else {}
    payload["images"] = [
        asset.get("url") if asset.get("persisted") else None for asset in result.assets
    ]
    return payload


def video_output_assets(generation_metadata: Any) -> list[dict[str, Any]]:
    if not isinstance(generation_metadata, dict):
        return []
    raw_assets = generation_metadata.get("assets")
    if not isinstance(raw_assets, dict):
        return []
    assets: list[dict[str, Any]] = []
    for role in ("video", "thumbnail", "last_frame"):
        raw = raw_assets.get(role)
        if not isinstance(raw, dict) or not raw.get("url"):
            continue
        assets.append(
            {
                "media_type": "video" if role == "video" else "image",
                "role": role,
                "url": _stable_url(raw.get("url")),
                "object_key": raw.get("object_key"),
                "file_size": raw.get("file_size"),
                "mime_type": raw.get("mime_type"),
                "sha256": raw.get("sha256"),
                "persisted": bool(raw.get("object_key")),
            }
        )
    return assets


def primary_video_persisted(assets: list[dict[str, Any]]) -> bool:
    return any(
        asset.get("role") == "video" and asset.get("persisted") for asset in assets
    )


def attach_invocation_id(response: Any, invocation_id: int | None) -> None:
    if response is None or invocation_id is None:
        return
    metadata = dict(getattr(response, "metadata", None) or {})
    metadata[INVOCATION_ID_KEY] = invocation_id
    response.metadata = metadata


def invocation_id_from_response(response: Any) -> int | None:
    metadata = getattr(response, "metadata", None)
    value = metadata.get(INVOCATION_ID_KEY) if isinstance(metadata, dict) else None
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


async def persist_image_asset(
    source: str,
    *,
    role: str,
    provider: str,
    model: str | None,
    prefix: str,
    logger: Any,
) -> dict[str, Any]:
    owned = _owned_oss_descriptor(source, role)
    if owned is not None:
        return owned
    try:
        metadata = build_generation_metadata(
            provider=provider,
            model=model,
            media_type="image",
            extra={"role": role, "source": "invocation_audit"},
        )
        if source.startswith("data:image"):
            header, encoded = source.split(",", 1)
            mime_type = header.split(";", 1)[0].split(":", 1)[-1]
            extension = mime_type.split("/", 1)[-1] or "png"
            uploaded = await upload_base64(
                base64_payload=encoded,
                filename=f"{role}.{extension}",
                media_type="image",
                prefix=prefix,
                metadata=metadata,
            )
        else:
            uploaded = await upload_from_url(
                url=source,
                media_type="image",
                prefix=prefix,
                metadata=metadata,
            )
        if uploaded and uploaded.get("success"):
            return _upload_descriptor(uploaded, role, source)
        error = (uploaded or {}).get("error") or "OSS service unavailable"
    except Exception as exc:
        error = str(exc)
        if logger is not None:
            logger.warning("Invocation media persistence failed role=%s: %s", role, exc)
    return {
        "media_type": "image",
        "role": role,
        "source_url": _stable_url(source),
        "url": None,
        "persisted": False,
        "error": error,
    }


def _owned_oss_descriptor(source: str, role: str) -> dict[str, Any] | None:
    from app.services.storage.oss_service import oss_service

    domain = str(getattr(oss_service, "domain", "") or "").rstrip("/")
    stable = _stable_url(source)
    if not domain or not stable or not stable.startswith(f"{domain}/"):
        return None
    return {
        "media_type": "image",
        "role": role,
        "source_url": stable,
        "url": stable,
        "object_key": stable[len(domain) + 1 :],
        "persisted": True,
    }


def _upload_descriptor(
    uploaded: dict[str, Any], role: str, source: str
) -> dict[str, Any]:
    metadata = uploaded.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    return {
        "media_type": "image",
        "role": role,
        "source_url": _stable_url(source),
        "url": _stable_url(uploaded.get("file_url")),
        "object_key": uploaded.get("object_key"),
        "file_size": uploaded.get("file_size"),
        "mime_type": uploaded.get("content_type") or metadata.get("mime_type"),
        "sha256": metadata.get("sha256"),
        "persisted": True,
    }


def _normalize_values(values: Any) -> list[str]:
    items = values if isinstance(values, list) else [values]
    normalized: list[str] = []
    for item in items:
        candidate = item
        if isinstance(item, dict):
            candidate = item.get("url") or item.get("image_url")
        if isinstance(candidate, str) and candidate.strip():
            normalized.append(candidate.strip())
    return normalized


def _stable_url(value: Any) -> str | None:
    if not isinstance(value, str) or value.startswith("data:"):
        return None
    try:
        parts = urlsplit(value)
        return parts._replace(query="", fragment="").geturl()
    except Exception:
        return value
