"""Video duration helpers.

Some providers only support discrete video durations (e.g. 4/6/8 seconds). To
avoid producing clips shorter than the storyboard timeline, we resolve the
provider duration using a ceil-to-allowed strategy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class VideoDurationResolution:
    """Resolved duration mapping for a single video clip."""

    target_seconds: float
    provider_seconds: int
    allowed_durations: list[int]
    needs_split: bool


def normalize_target_seconds(value: Any, *, default: float = 5.0) -> float:
    """Normalize a user/storyboard duration input into seconds (float)."""
    try:
        dur = float(value)
    except (TypeError, ValueError):
        return float(default)
    if dur <= 0:
        return float(default)
    return dur


def _unique_sorted_ints(values: Iterable[Any]) -> list[int]:
    resolved: list[int] = []
    seen: set[int] = set()
    for item in values:
        try:
            v = int(item)
        except (TypeError, ValueError):
            continue
        if v <= 0 or v in seen:
            continue
        seen.add(v)
        resolved.append(v)
    resolved.sort()
    return resolved


def resolve_duration_ceil(
    *,
    target_seconds: float,
    allowed_durations: Sequence[int],
) -> VideoDurationResolution:
    """Resolve provider duration using ceil-to-allowed strategy.

    Rules:
    - If target <= min allowed -> use min allowed (trim later if needed)
    - If target between -> use smallest allowed >= target
    - If target > max allowed -> use max allowed and mark needs_split
    """
    target = normalize_target_seconds(target_seconds)
    allowed = _unique_sorted_ints(allowed_durations)
    if not allowed:
        # No constraints; keep best-effort int seconds for provider.
        provider_seconds = int(target + 0.999999)
        return VideoDurationResolution(
            target_seconds=target,
            provider_seconds=max(1, provider_seconds),
            allowed_durations=[],
            needs_split=False,
        )

    min_allowed = allowed[0]
    max_allowed = allowed[-1]

    needs_split = target > max_allowed
    if target <= min_allowed:
        return VideoDurationResolution(
            target_seconds=target,
            provider_seconds=min_allowed,
            allowed_durations=allowed,
            needs_split=False,
        )

    for candidate in allowed:
        if candidate >= target:
            return VideoDurationResolution(
                target_seconds=target,
                provider_seconds=candidate,
                allowed_durations=allowed,
                needs_split=False,
            )

    return VideoDurationResolution(
        target_seconds=target,
        provider_seconds=max_allowed,
        allowed_durations=allowed,
        needs_split=needs_split,
    )

