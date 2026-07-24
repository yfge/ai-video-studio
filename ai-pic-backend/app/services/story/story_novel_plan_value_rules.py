"""Scalar predicate and JSON-value rules for chapter plans."""

from typing import Any

_ENCODED_JSON_VALUES = {"null", "[]", "{}"}


def predicate_matches(actual: Any, operator: str, expected: Any) -> bool:
    if operator == "eq":
        return actual == expected
    if operator == "ne":
        return actual != expected
    if operator == "contains":
        return expected in (actual or [])
    return expected not in (actual or [])


def reject_encoded_json(value: Any, position: int) -> None:
    if isinstance(value, str) and value.strip().lower() in _ENCODED_JSON_VALUES:
        raise ValueError(
            f"第 {position} 章状态值必须使用真实 JSON 类型，不能写字符串 {value!r}"
        )
