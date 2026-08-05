"""Apply Canon ``contains`` outcomes to JSON list or relationship-map state."""

from __future__ import annotations

import copy
from typing import Any


def merge_contains_outcome(current: Any, field: str, value: Any) -> Any:
    if field == "relationships":
        member_id = _relationship_member_id(value)
        if not member_id or current is not None and not isinstance(current, dict):
            raise ValueError("relationship contains outcome 必须是 关系:实体ID")
        result = copy.deepcopy(current or {})
        result[member_id] = copy.deepcopy(value)
        return result
    if current is None:
        current = []
    if not isinstance(current, (list, tuple, set)):
        raise ValueError("contains outcome 目标不是数组")
    result = list(current)
    if value not in result:
        result.append(copy.deepcopy(value))
    return result


def contains_outcome_matches(current: Any, field: str, value: Any) -> bool:
    if field == "relationships" and isinstance(current, dict):
        member_id = _relationship_member_id(value)
        return bool(member_id and current.get(member_id) == value)
    return isinstance(current, (list, tuple, set)) and value in current


def _relationship_member_id(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    relation, separator, member_id = value.rpartition(":")
    return member_id if separator and relation and member_id else None
