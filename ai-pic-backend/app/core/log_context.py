"""Shared structured logging context."""

from __future__ import annotations

from contextvars import ContextVar

DEFAULTS = {
    "request_id": "no-request-id",
    "url": "no-url",
    "client_ip": "no-client-ip",
    "run_id": "no-run-id",
    "task_id": "no-task-id",
    "route": "no-route",
    "story_business_id": "no-story",
    "episode_business_id": "no-episode",
    "script_business_id": "no-script",
    "provider": "no-provider",
    "model": "no-model",
    "stage": "no-stage",
    "timing_source": "no-timing-source",
    "status": "no-status",
    "latency_ms": "0",
}

_VARS = {key: ContextVar(key, default=value) for key, value in DEFAULTS.items()}


def set_log_context(**kwargs: str | int | None) -> None:
    for key, value in kwargs.items():
        if key not in _VARS or value is None:
            continue
        _VARS[key].set(str(value))


def reset_log_context() -> None:
    for key, default in DEFAULTS.items():
        _VARS[key].set(default)


def get_log_context() -> dict[str, str]:
    return {key: var.get() for key, var in _VARS.items()}
