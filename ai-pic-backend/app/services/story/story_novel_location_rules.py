"""Shared location rules for planned and extracted long-form state."""

from __future__ import annotations

ABSENT_OBJECT_STATUS_LITERALS = (
    "不存在",
    "尚未存在",
    "尚未创建",
    "未创建",
    "absent",
    "not-created",
    "not-yet-created",
)
_ABSENT_OBJECT_STATUSES = set(ABSENT_OBJECT_STATUS_LITERALS)
TERMINAL_OBJECT_STATUS_LITERALS = (
    "consumed",
    "destroyed",
    "exhausted",
    "melted",
    "spent",
    "不存在",
    "已消耗",
    "已熔毁",
    "已销毁",
)
_TERMINAL_OBJECT_STATUSES = set(TERMINAL_OBJECT_STATUS_LITERALS)


def entity_kinds(canon: dict) -> dict[str, str]:
    return {
        item["id"]: item["kind"]
        for item in canon.get("entities") or []
        if item.get("id") and item.get("kind")
    }


def initial_statuses(canon: dict) -> dict[str, object]:
    return {
        subject_id: state["status"]
        for subject_id, state in (canon.get("initial_state") or {}).items()
        if isinstance(state, dict) and "status" in state
    }


def location_context(canon: dict) -> dict:
    kinds = entity_kinds(canon)
    return {
        "entity_kinds": kinds,
        "initial_statuses": initial_statuses(canon),
        "locations": {
            subject_id for subject_id, kind in kinds.items() if kind == "location"
        },
    }


def movement_start_state(chapter: dict, subjects: dict) -> dict[str, dict]:
    return {
        item["subject_id"]: dict(subjects.get(item["subject_id"]) or {})
        for item in chapter.get("location_transitions") or []
    }


def planned_movement_issue(
    chapter: dict,
    movement: dict,
    *,
    kinds: dict[str, str],
    initial: dict[str, object],
    locations: set[str],
    current_location: str | None,
    current_status: object,
) -> str | None:
    invalid = {
        location_id
        for location_id in (
            movement.get("from_location_id"),
            movement.get("to_location_id"),
        )
        if location_id is not None and location_id not in locations
    }
    if movement.get("to_location_id") is None:
        invalid.add(None)
    if invalid:
        return (
            f"地点引用无效: {sorted(invalid, key=str)}；"
            f"只能使用 Canon locations: {sorted(locations)}"
        )
    origin = movement.get("from_location_id")
    if not str(movement.get("means") or "").strip():
        return f"地点移动缺少有效过程: {movement}"
    if origin is None:
        if not is_initial_object_placement(
            chapter,
            movement,
            kinds=kinds,
            initial=initial,
            current_location=current_location,
            current_status=current_status,
        ):
            return f"地点起点不连续: {movement}"
    elif current_location != origin:
        return f"地点起点不连续: {movement}"
    if origin == movement.get("to_location_id"):
        return f"地点移动起终点相同: {movement}"
    return None


def is_initial_object_placement(
    chapter: dict,
    movement: dict,
    *,
    kinds: dict[str, str],
    initial: dict[str, object],
    current_location: str | None,
    current_status: object,
) -> bool:
    subject_id = movement.get("subject_id")
    if (
        movement.get("from_location_id") is not None
        or current_location is not None
        or kinds.get(subject_id) != "object"
        or not _is_absent(initial.get(subject_id))
        or not _is_absent(current_status)
    ):
        return False
    transitions = [
        transition
        for transition in chapter.get("state_transitions") or []
        if transition.get("subject_id") == subject_id
        and transition.get("field") == "status"
    ]
    movements = [
        item
        for item in chapter.get("location_transitions") or []
        if item.get("subject_id") == subject_id
    ]
    return (
        len(transitions) == 1
        and len(movements) == 1
        and movements[0] == movement
        and transitions[0].get("from_value") == current_status
        and _is_absent(transitions[0].get("from_value"))
        and _is_present_creation_status(transitions[0].get("to_value"))
        and bool(str(transitions[0].get("reason") or "").strip())
    )


def _is_absent(value) -> bool:
    if not isinstance(value, str):
        return False
    return value in _ABSENT_OBJECT_STATUSES


def _is_present_creation_status(value) -> bool:
    if not isinstance(value, str) or value != value.strip() or not value:
        return False
    return not _is_absent(value) and value.lower() not in _TERMINAL_OBJECT_STATUSES
