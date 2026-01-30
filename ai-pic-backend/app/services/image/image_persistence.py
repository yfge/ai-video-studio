"""
Image persistence utilities.

Provides functions for downloading, saving, and uploading images
to local storage and OSS.
"""

import asyncio
import base64
import hashlib
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import unquote

import aiofiles
import httpx
from app.core.config import settings
from app.core.logging import get_logger
from app.services.media import build_generation_metadata
from app.services.media import upload_bytes as upload_media_bytes
from app.services.storage import oss_service
from app.utils.url_utils import normalize_presigned_url

logger = get_logger()


async def download_image(
    image_data: str,
    ip_name: str,
    category: str,
) -> str:
    """
    Download image from URL or decode base64 and save to local file.

    Args:
        image_data: Image URL or base64-encoded data.
        ip_name: Name for logging context.
        category: Image category for logging context.

    Returns:
        Local file path where image was saved.

    Raises:
        RuntimeError: If image download/processing fails after retries.
    """
    file_extension = ".png"
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"

    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    local_file_path = os.path.join(upload_dir, unique_filename)

    # Handle base64 data
    if image_data.startswith("data:image"):
        logger.info("Processing base64 image data")
        base64_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(base64_data)

        async with aiofiles.open(local_file_path, "wb") as f:
            await f.write(image_bytes)
        logger.info("Base64 image saved to: %s", local_file_path)
        return local_file_path

    # Handle URL with retry
    normalized_url = unquote(image_data) if "%25" in image_data else image_data
    normalized_url = normalize_presigned_url(normalized_url)
    last_error: Exception | None = None

    for attempt in range(3):
        try:
            logger.info(
                "Downloading image URL (attempt %s): %s...",
                attempt + 1,
                normalized_url[:100],
            )
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(normalized_url, timeout=60.0)
                response.raise_for_status()

            async with aiofiles.open(local_file_path, "wb") as f:
                await f.write(response.content)

            logger.info("Image saved to: %s", local_file_path)
            return local_file_path

        except Exception as exc:
            last_error = exc
            logger.warning(
                "Image download failed attempt=%s url=%s err=%s",
                attempt + 1,
                normalized_url,
                exc,
            )
            if attempt < 2:
                await asyncio.sleep(1.5 * (attempt + 1))

    raise RuntimeError(f"Image processing failed: {last_error}")


async def upload_local_image_to_oss(
    local_file_path: str,
    *,
    prefix: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Upload a local image file to OSS.

    Args:
        local_file_path: Path to local image file.
        prefix: OSS path prefix.
        metadata: Optional metadata to attach.

    Returns:
        OSS upload result dictionary.

    Raises:
        RuntimeError: If OSS service not configured or upload fails.
    """
    service = oss_service
    if not service:
        raise RuntimeError("OSS service not configured, cannot upload image")

    try:
        with open(local_file_path, "rb") as f:
            file_content = f.read()
    except Exception as exc:
        raise RuntimeError(f"Failed to read local image: {exc}") from exc

    filename = os.path.basename(local_file_path)

    sha256 = hashlib.sha256(file_content).hexdigest()
    extra = dict(metadata or {})
    provider = str(extra.get("provider") or "unknown")
    model_val = extra.get("model")
    model = str(model_val) if model_val is not None else None
    oss_result = await upload_media_bytes(
        content=file_content,
        filename=filename,
        media_type="image",
        prefix=prefix,
        metadata=build_generation_metadata(
            provider=provider,
            model=model,
            media_type="image",
            sha256=sha256,
            extra=extra,
        ),
        oss_service_override=service,
    )

    if not oss_result or not oss_result.get("success"):
        raise RuntimeError(f"OSS upload failed: {oss_result}")

    return oss_result


async def persist_local_image(
    local_file_path: str,
    *,
    prefix: str,
    metadata: Optional[Dict[str, Any]] = None,
    require_upload: bool = False,
) -> Dict[str, Any]:
    """
    Persist an existing local image file with optional OSS upload.

    Args:
        local_file_path: Path to local image file.
        prefix: OSS path prefix for upload.
        metadata: Optional metadata.
        require_upload: If True, raises error when OSS upload fails.

    Returns:
        Dictionary with local path, relative path, file size, and OSS info.
    """
    file_size = os.path.getsize(local_file_path)
    filename = os.path.basename(local_file_path)
    relative_path = f"/uploads/{filename}"

    oss_result = None
    oss_url = None

    if oss_service:
        try:
            oss_result = await upload_local_image_to_oss(
                local_file_path,
                prefix=prefix,
                metadata=metadata or {},
            )
            success = bool(oss_result.get("success"))
            file_url = oss_result.get("file_url")

            if success and file_url:
                oss_url = file_url
                logger.info(
                    "CDN upload success | filename=%s object_key=%s url=%s prefix=%s",
                    filename,
                    oss_result.get("object_key"),
                    file_url,
                    prefix,
                )
            elif require_upload:
                raise RuntimeError(f"OSS upload failed: {oss_result}")
            else:
                logger.warning(
                    "OSS upload returned no URL, using local path | filename=%s result=%s",
                    filename,
                    oss_result,
                )
        except Exception as exc:
            if require_upload:
                raise
            logger.warning("OSS upload exception, using local path: %s", exc)
    elif require_upload:
        raise RuntimeError("OSS not configured, cannot upload image")
    else:
        logger.info(
            "OSS/CDN not configured, using local path | filename=%s path=%s",
            filename,
            relative_path,
        )

    return {
        "local_file_path": local_file_path,
        "relative_path": relative_path,
        "file_size": file_size,
        "filename": filename,
        "oss_url": oss_url,
        "oss_upload": oss_result,
    }


async def persist_generated_image(
    image_data: str,
    *,
    ip_name: str,
    category: str,
    prefix: str,
    metadata: Optional[Dict[str, Any]] = None,
    require_upload: bool = False,
) -> Dict[str, Any]:
    """
    Download/save generated image and optionally upload to OSS.

    Args:
        image_data: Image URL or base64 data.
        ip_name: Character name for context.
        category: Image category.
        prefix: OSS path prefix.
        metadata: Optional metadata.
        require_upload: If True, raises error when OSS upload fails.

    Returns:
        Dictionary with paths and metadata.
    """
    local_file_path = await download_image(image_data, ip_name, category)
    return await persist_local_image(
        local_file_path,
        prefix=prefix,
        metadata=metadata,
        require_upload=require_upload,
    )


async def persist_uploaded_image(
    file_bytes: bytes,
    original_filename: str,
    *,
    prefix: str,
    metadata: Optional[Dict[str, Any]] = None,
    require_upload: bool = False,
) -> Dict[str, Any]:
    """
    Persist user-uploaded image file.

    Args:
        file_bytes: Raw file bytes.
        original_filename: Original upload filename.
        prefix: OSS path prefix.
        metadata: Optional metadata.
        require_upload: If True, raises error when OSS upload fails.

    Returns:
        Dictionary with paths and metadata.
    """
    ext = os.path.splitext(original_filename)[1].lower() or ".png"
    unique_filename = f"{uuid.uuid4().hex}{ext}"

    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    local_file_path = os.path.join(upload_dir, unique_filename)

    async with aiofiles.open(local_file_path, "wb") as f:
        await f.write(file_bytes)

    logger.info("Uploaded image saved to: %s", local_file_path)

    return await persist_local_image(
        local_file_path,
        prefix=prefix,
        metadata=metadata,
        require_upload=require_upload,
    )


async def save_base64_image(base64_data: str, source: str) -> str:
    """
    Save base64-encoded image to local file.

    Args:
        base64_data: Base64-encoded image data (without data URI prefix).
        source: Source identifier for filename.

    Returns:
        Path to saved file.
    """
    image_bytes = base64.b64decode(base64_data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ai_generated_{source}_{timestamp}.png"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    with open(filepath, "wb") as f:
        f.write(image_bytes)

    return f"/uploads/{filename}"
