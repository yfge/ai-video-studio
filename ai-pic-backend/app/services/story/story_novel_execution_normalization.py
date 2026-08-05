"""Normalize unambiguous model aliases in event execution contracts."""

_ALIASES = {
    ("action_phase", "active"): "progress",
    ("action_phase", "activity"): "progress",
    ("action_phase", "ongoing"): "progress",
    ("action_phase", "progressive"): "progress",
    ("action_phase", "reaction"): "instant",
    ("time_scope", "day"): "same_day",
    ("time_scope", "short"): "same_day",
    ("time_scope", "current_chapter"): "unspecified",
    ("effort", "medium"): "moderate",
}


def normalize_execution_aliases(executions: list[dict]) -> None:
    for execution in executions:
        for field in ("action_phase", "time_scope", "effort"):
            value = execution.get(field)
            execution[field] = _ALIASES.get((field, value), value)
