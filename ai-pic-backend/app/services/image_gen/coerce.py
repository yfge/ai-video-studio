from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def clean_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def maybe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def coerce_str_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence):
        return [item for item in value if isinstance(item, str)]
    return []


def value_from_payload(payload: Mapping[str, Any], key: str, fallback: Any) -> Any:
    """Read a key from payload with fallback, preserving explicit nulls."""
    return payload[key] if key in payload else fallback
