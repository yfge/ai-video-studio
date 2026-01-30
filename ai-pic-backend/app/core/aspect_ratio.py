from __future__ import annotations

from typing import Literal, Optional

AspectRatio = Literal["9:16", "16:9"]
DEFAULT_ASPECT_RATIO: AspectRatio = "9:16"


def resolve_aspect_ratio(
    *,
    request_value: Optional[str],
    episode_value: Optional[str],
    story_value: Optional[str],
) -> AspectRatio:
    """Resolve aspect ratio with priority: request > episode > story > default.

    We intentionally normalize any unexpected values back to DEFAULT_ASPECT_RATIO,
    so legacy/dirty DB values do not break generation requests.
    """

    for raw in (request_value, episode_value, story_value):
        if raw is None:
            continue
        value = raw.strip()
        if value in ("9:16", "16:9"):
            return value  # type: ignore[return-value]

    return DEFAULT_ASPECT_RATIO
