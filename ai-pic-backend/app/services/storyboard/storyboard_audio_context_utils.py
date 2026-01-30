from __future__ import annotations

from typing import Any, Iterable, Optional


def compact(text: str) -> str:
    return " ".join((text or "").strip().split())


def truncate(text: str, limit: int) -> str:
    if not text:
        return ""
    value = compact(text)
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "..."


def dedupe_strs(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    for item in items or []:
        if not isinstance(item, str):
            continue
        value = item.strip()
        if not value or value in out:
            continue
        out.append(value)
    return out


def pick_first_url(value: Any) -> Optional[str]:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                return item.strip()
    return None

