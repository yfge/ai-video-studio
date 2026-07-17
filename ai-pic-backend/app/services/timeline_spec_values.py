"""Primitive value normalization shared by Timeline Spec builders."""

from typing import Any


def int_ms(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def slug(value: Any) -> str:
    raw = str(value if value is not None else "unknown").strip().lower()
    safe = [ch if ch.isalnum() else "_" for ch in raw]
    return "".join(safe).strip("_") or "unknown"
