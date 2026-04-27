"""Small helpers shared by LangGraph-backed generation pipelines."""

from __future__ import annotations

from typing import Any, Dict


def has_state_error(state: Dict[str, Any]) -> bool:
    """Return true when a graph state carries a terminal error marker."""
    return bool(state.get("error"))


def route_on_error(
    state: Dict[str, Any],
    *,
    ok: str,
    error: str,
) -> str:
    """Route to ``error`` when the current state has a terminal error."""
    return error if has_state_error(state) else ok


def end_on_error_router(ok: str, end: Any):
    """Return a LangGraph router that stops at ``end`` when state has an error."""

    def _route(state: Dict[str, Any]):
        return end if has_state_error(state) else ok

    return _route


def reset_control_flags(
    state: Dict[str, Any],
    *flags: str,
) -> Dict[str, Any]:
    """Return a shallow state copy with transient graph control flags cleared."""
    updated = dict(state)
    for flag in flags:
        updated[flag] = False
    return updated


def append_reasoning(
    state: Dict[str, Any],
    step: str,
    *,
    clear_flags: tuple[str, ...] = (),
    **updates: Any,
) -> Dict[str, Any]:
    """Return state with optional flag reset, updates, and one reasoning step."""
    updated = reset_control_flags(state, *clear_flags) if clear_flags else dict(state)
    updated.update(updates)
    updated["reasoning"] = state.get("reasoning", []) + [step]
    return updated
