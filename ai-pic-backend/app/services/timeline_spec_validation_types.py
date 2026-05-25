"""Shared helpers for Timeline Spec validation."""

from __future__ import annotations

from typing import Any


class TimelineSpecValidationError(ValueError):
    def __init__(self, code: str, path: str, message: str):
        self.code = code
        self.path = path
        self.message = message
        super().__init__(f"{code} at {path}: {message}")

    def to_detail(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


def required_int(data: dict[str, Any], key: str, path: str, *, min_value: int) -> int:
    try:
        value = int(data[key])
    except (KeyError, TypeError, ValueError):
        fail("timeline_spec_field_invalid", path, f"{key} must be an integer")
    if value < min_value:
        fail("timeline_spec_field_invalid", path, f"{key} must be >= {min_value}")
    return value


def required_string(data: dict[str, Any], key: str, path: str) -> str:
    value = data.get(key)
    if not non_empty_string(value):
        fail("timeline_spec_field_missing", path, f"{key} is required")
    return str(value)


def required_present(data: dict[str, Any], key: str, path: str) -> None:
    if data.get(key) is None or data.get(key) == "":
        fail("timeline_spec_field_missing", path, f"{key} is required")


def match_optional_id(data: dict[str, Any], key: str, expected: int | None) -> None:
    if expected is None:
        return
    value = required_int(data, key, key, min_value=1)
    if value != expected:
        fail("timeline_spec_identity_mismatch", key, f"{key} must be {expected}")


def match_required_source_value(
    clip: dict[str, Any],
    source: dict[str, Any],
    key: str,
    path: str,
) -> None:
    required_present(source, key, path)
    match_value(
        source.get(key), clip.get(key), path, f"source.{key} must match clip {key}"
    )


def match_value(value: Any, expected: Any, path: str, message: str) -> None:
    if str(value) != str(expected):
        fail("timeline_spec_source_mismatch", path, message)


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def fail(code: str, path: str, message: str) -> None:
    raise TimelineSpecValidationError(code, path, message)
