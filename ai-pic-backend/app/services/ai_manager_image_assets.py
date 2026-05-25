"""Image asset helpers used by AI manager generation flows."""

from __future__ import annotations

from typing import Any


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
