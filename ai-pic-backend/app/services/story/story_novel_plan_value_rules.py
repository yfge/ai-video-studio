"""Scalar predicate and JSON-value rules for chapter plans."""

from typing import Any

_ENCODED_JSON_VALUES = {"null", "[]", "{}"}
_PREDICATE_OPERATOR_ALIASES = {"equals": "eq"}


def normalize_predicate_operators(chapter: dict) -> dict:
    """Translate only unambiguous provider aliases before strict schema parsing."""
    normalized = dict(chapter)
    normalized["preconditions"] = [
        (
            {
                **item,
                "operator": _predicate_operator(item),
            }
            if isinstance(item, dict)
            else item
        )
        for item in chapter.get("preconditions") or []
    ]
    return normalized


def _predicate_operator(item: dict):
    operator = item.get("operator")
    if operator == "not_exists" and item.get("value") is None:
        return "eq"
    return _PREDICATE_OPERATOR_ALIASES.get(operator, operator)


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
