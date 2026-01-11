from __future__ import annotations

import hashlib
from typing import Sequence
from urllib.parse import urlparse, urlunparse

DEFAULT_ALLOWED_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg")
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0"}


def _rewrite_localhost_url(url: str, *, backend_base: str) -> str:
    base = (backend_base or "").rstrip("/")
    if not base:
        return url
    parsed = urlparse(url)
    if parsed.hostname not in _LOCAL_HOSTS:
        return url
    base_parsed = urlparse(base)
    if not base_parsed.scheme or not base_parsed.netloc:
        return url
    rebuilt = parsed._replace(netloc=base_parsed.netloc, scheme=base_parsed.scheme)
    return urlunparse(rebuilt)


def normalize_reference_images(
    refs: Sequence[str],
    *,
    backend_base: str,
    allowed_ext: tuple[str, ...] = DEFAULT_ALLOWED_EXT,
) -> list[str]:
    """Normalize reference image inputs to absolute URLs when possible.

    Keeps http(s)/data:image URLs. Converts relative paths ending with a known image
    extension to `{backend_base}/{path}`. Filters out descriptive strings.
    """
    base = (backend_base or "").rstrip("/")
    normalized: list[str] = []
    for raw in refs or []:
        if not isinstance(raw, str):
            continue
        ref_url = raw.strip()
        if not ref_url:
            continue
        lower = ref_url.lower()
        base_path = lower.split("?", 1)[0]
        if lower.startswith(("http://", "https://", "data:image/")):
            if lower.startswith("data:image/"):
                normalized.append(ref_url)
            else:
                normalized.append(_rewrite_localhost_url(ref_url, backend_base=base))
            continue
        if base_path.endswith(allowed_ext):
            path = ref_url if ref_url.startswith("/") else f"/{ref_url}"
            normalized.append(f"{base}{path}" if base else path)
    return normalized


def resolve_base_image(base_image: str, *, backend_base: str) -> str:
    """Resolve a base image (url/data/path) into an absolute URL when possible."""
    raw = (base_image or "").strip()
    if not raw:
        return ""
    lower = raw.lower()
    if lower.startswith(("http://", "https://", "data:image/")):
        if lower.startswith("data:image/"):
            return raw
        return _rewrite_localhost_url(raw, backend_base=backend_base)
    base = (backend_base or "").rstrip("/")
    path = raw if raw.startswith("/") else f"/{raw}"
    return f"{base}{path}" if base else path


def hash_reference_images(urls: Sequence[str]) -> list[str]:
    """Return stable short hashes for reference images without storing URLs."""
    hashed: list[str] = []
    for url in urls or []:
        if not isinstance(url, str) or not url:
            continue
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        hashed.append(digest[:12])
    return hashed
