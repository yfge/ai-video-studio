"""
Virtual IP Images helper functions.

Shared utilities for virtual IP image operations including validation,
identifier parsing, and URL handling.
"""

from typing import Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPImage


def not_deleted(query, model):
    """Filter out soft-deleted rows."""
    return query.filter(model.is_deleted.is_(False))


def parse_identifier(
    identifier: int | str | None,
) -> Tuple[Optional[int], Optional[str]]:
    """Parse identifier to (id, business_id) tuple."""
    if identifier is None:
        return None, None
    if isinstance(identifier, int):
        return identifier, None
    raw = str(identifier).strip()
    if not raw:
        return None, None
    if raw.isdigit():
        try:
            return int(raw), None
        except Exception:
            return None, raw
    return None, raw


def get_owned_virtual_ip(
    db: Session,
    current_user: User,
    virtual_ip_identifier: int | str | None,
    virtual_ip_business_id: Optional[str] = None,
) -> VirtualIP:
    """Get virtual IP owned by current user (supports business_id)."""
    vid, biz = parse_identifier(virtual_ip_identifier)
    if virtual_ip_business_id:
        biz = virtual_ip_business_id
    query = not_deleted(db.query(VirtualIP), VirtualIP)
    if biz:
        query = query.filter(VirtualIP.business_id == biz)
    elif vid is not None:
        query = query.filter(VirtualIP.id == vid)
    else:
        raise HTTPException(status_code=400, detail="虚拟IP标识缺失")
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(VirtualIP.user_id == current_user.id)
    vip = query.first()
    if not vip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    return vip


def get_virtual_ip_image(
    db: Session,
    virtual_ip: VirtualIP,
    image_id: Optional[int],
    image_business_id: Optional[str],
) -> VirtualIPImage:
    """Get virtual IP image by ID or business_id."""
    query = not_deleted(db.query(VirtualIPImage), VirtualIPImage).filter(
        VirtualIPImage.virtual_ip_id == virtual_ip.id
    )
    if image_business_id:
        query = query.filter(VirtualIPImage.business_id == image_business_id)
    elif image_id is not None:
        query = query.filter(VirtualIPImage.id == image_id)
    else:
        raise HTTPException(status_code=400, detail="图像标识缺失")
    image = query.first()
    if not image:
        raise HTTPException(status_code=404, detail="虚拟IP图像不存在")
    return image


def resolve_image_url(image: VirtualIPImage) -> Optional[str]:
    """Resolve image URL (prefer OSS, fallback to local path)."""
    if not image:
        return None
    return image.oss_url or image.file_path


def set_ip_default_avatar(
    db: Session, virtual_ip_id: int, image: VirtualIPImage
) -> None:
    """Update virtual IP default avatar URL."""
    url = resolve_image_url(image)
    if not url:
        return
    db.query(VirtualIP).filter(VirtualIP.id == virtual_ip_id).update(
        {"default_avatar_url": url},
        synchronize_session=False,
    )


def normalize_reference_images(refs: list[str], backend_base: str) -> list[str]:
    """Filter valid reference image URLs.

    Only keeps http(s)/data:image URLs or paths with image extensions.
    """
    allowed_ext = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg")
    normalized: list[str] = []
    for raw in refs:
        if not isinstance(raw, str):
            continue
        ref_url = raw.strip()
        if not ref_url:
            continue
        lower = ref_url.lower()
        base_path = lower.split("?", 1)[0]
        if lower.startswith(("http://", "https://", "data:image/")):
            normalized.append(ref_url)
        elif base_path.endswith(allowed_ext):
            path = ref_url if ref_url.startswith("/") else f"/{ref_url}"
            normalized.append(f"{backend_base}{path}")
        # Non-URL/no-extension descriptive strings are ignored to avoid 404
    return normalized
