"""Image asset helpers used by AI manager generation flows."""

from __future__ import annotations

import base64
from typing import Any

from app.services.ai_manager_logging import truncate


def prefer_http_for_download(url: str) -> str:
    if isinstance(url, str) and url.lower().startswith("https://"):
        return "http://" + url[len("https://") :]
    return url


def maybe_compress_inline_image(
    raw: bytes,
    *,
    content_type: str,
    target_max_bytes: int,
    max_side: int,
) -> tuple[bytes, str]:
    """
    Compress large reference images for inline/base64 transport.

    Some providers/proxies enforce strict request size limits. This helper tries
    to downscale and re-encode as JPEG when the payload is too large.
    """
    if not raw or len(raw) <= target_max_bytes:
        return raw, content_type or "image/png"

    try:
        from io import BytesIO

        from PIL import Image, ImageOps

        img = Image.open(BytesIO(raw))
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        w, h = img.size
        max_current = max(w, h) if w and h else 0
        if max_current and max_current > max_side:
            scale = max_side / float(max_current)
            new_w = max(1, int(round(w * scale)))
            new_h = max(1, int(round(h * scale)))
            img = img.resize((new_w, new_h), Image.LANCZOS)

        for quality in (85, 75, 65):
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            out = buf.getvalue()
            if out and len(out) <= target_max_bytes:
                return out, "image/jpeg"

        buf = BytesIO()
        img.save(buf, format="JPEG", quality=60, optimize=True)
        out = buf.getvalue()
        if out:
            return out, "image/jpeg"
    except Exception:
        pass

    return raw, content_type or "image/png"


async def preload_image_references_as_data_urls(
    *,
    image_url: str,
    extra_images: list[Any],
    prefer_provider: str | None,
    available_providers: list[str],
    timeout: float,
    logger: Any,
) -> list[str]:
    """Preload image-to-image references as data URLs for provider payloads."""
    base64_images: list[str] = []
    try:
        urls_raw = [image_url] + list(extra_images or [])
        urls: list[str] = []
        for url in urls_raw:
            if not url:
                continue
            if url not in urls:
                urls.append(url)

        if not urls:
            return []

        import httpx

        prefer_is_google = (prefer_provider or "").lower() == "google"
        maybe_google = prefer_is_google or ("google" in available_providers)
        max_refs = 4 if prefer_is_google else (8 if maybe_google else 14)
        target_max_bytes = (
            220_000 if prefer_is_google else (350_000 if maybe_google else 2_000_000)
        )
        max_side = 512 if prefer_is_google else (768 if maybe_google else 2048)

        async with httpx.AsyncClient(
            timeout=timeout,
            trust_env=False,
            follow_redirects=True,
        ) as client:
            for url in urls[:max_refs]:
                download_url = prefer_http_for_download(url)
                try:
                    resp = await client.get(download_url)
                    resp.raise_for_status()
                except Exception as e:
                    logger.warning(
                        "image_to_image base64 preload skip url=%s error=%s",
                        truncate(str(download_url), 256),
                        e,
                    )
                    continue

                ctype = resp.headers.get("Content-Type", "image/png")
                content, ctype = maybe_compress_inline_image(
                    resp.content,
                    content_type=ctype,
                    target_max_bytes=target_max_bytes,
                    max_side=max_side,
                )
                subtype = "png"
                if "/" in ctype:
                    subtype = (ctype.split("/", 1)[1].split(";", 1)[0] or "png").strip()
                b64 = base64.b64encode(content).decode("ascii")
                base64_images.append(f"data:image/{subtype.lower()};base64,{b64}")

        if not base64_images:
            logger.warning(
                "image_to_image base64 preload finished with no valid images | urls=%s",
                [truncate(str(url), 128) for url in urls],
            )
    except Exception as e:
        logger.warning("image_to_image base64 preload failed: %s", e)

    return base64_images


async def convert_base64_images_to_oss(
    images: Any,
    *,
    prefix: str = "ai-generated",
    logger: Any,
) -> list[str]:
    """
    Convert data URL images to OSS URLs, while preserving existing URL inputs.
    """
    if not images:
        return []

    normalized_images: list[str] = []
    raw_images: list[Any]
    if isinstance(images, list):
        raw_images = images
    else:
        raw_images = [images]

    for img in raw_images:
        candidate: Any = img
        if isinstance(img, dict):
            candidate = img.get("url") or img.get("image_url")
        if candidate is None:
            continue
        if not isinstance(candidate, str):
            candidate = str(candidate)
        candidate = candidate.strip()
        if not candidate:
            continue
        normalized_images.append(candidate)

    if not normalized_images:
        return []

    from app.services.storage.oss_service import oss_service

    if not oss_service:
        logger.warning("OSS service not available, returning original images")
        return normalized_images

    result_urls: list[str] = []

    for img in normalized_images:
        if not img.startswith("data:image"):
            result_urls.append(img)
            continue

        try:
            header, b64_data = img.split(",", 1)
            mime_part = header.split(";")[0]
            mime_type = mime_part.split(":")[1] if ":" in mime_part else "image/png"
            ext = mime_type.split("/")[1] if "/" in mime_type else "png"

            from app.services.media import build_generation_metadata
            from app.services.media import upload_base64 as upload_media_base64

            upload_result = await upload_media_base64(
                base64_payload=b64_data,
                filename=f"generated.{ext}",
                media_type="image",
                prefix=prefix,
                metadata=build_generation_metadata(
                    provider="unknown",
                    model=None,
                    media_type="image",
                    mime_type=mime_type,
                    extra={"source": "base64"},
                ),
                oss_service_override=oss_service,
            )

            if upload_result.get("success"):
                oss_url = upload_result.get("file_url")
                result_urls.append(oss_url)
                approx_size = len(b64_data) * 3 // 4
                logger.info(
                    "Converted base64 image to OSS URL | size=%d url=%s",
                    approx_size,
                    oss_url,
                )
            else:
                logger.warning(
                    "Failed to upload base64 image to OSS: %s",
                    upload_result.get("error"),
                )
                result_urls.append(img)

        except Exception as e:
            logger.error("Error converting base64 to OSS URL: %s", e)
            result_urls.append(img)

    return result_urls
