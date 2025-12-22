"""
URL helpers.

Normalize presigned URLs to avoid HTTP client double-encoding.
"""

from __future__ import annotations

from urllib.parse import quote, urlsplit, urlunsplit

SAFE_QUERY_CHARS = "!$&'()*+,;=:@?[]%"


def normalize_presigned_url(url: str) -> str:
    """Normalize presigned URLs by encoding unsafe query characters."""
    if not isinstance(url, str):
        return url
    if url.startswith("data:image"):
        return url
    try:
        parts = urlsplit(url)
    except Exception:
        return url
    if not parts.query:
        return url
    normalized_query = quote(parts.query, safe=SAFE_QUERY_CHARS)
    if normalized_query == parts.query:
        return url
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, normalized_query, parts.fragment)
    )
