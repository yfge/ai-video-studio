from __future__ import annotations

import re
from typing import Any, Dict, Optional

_WHITESPACE_RE = re.compile(r"\s+")


def _compact_text(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value).strip()


def build_episode_summary(
    payload: Dict[str, Any],
    *,
    max_chars: int = 1200,
) -> Optional[str]:
    """Build a stable, short episode summary for continuity/context injection.

    Prefer the model-provided `summary`. Fall back to plot_points / conflicts when
    legacy payloads omit `summary`.
    """

    summary = payload.get("summary")
    if isinstance(summary, str):
        summary = _compact_text(summary)
        if summary:
            return summary[:max_chars]

    plot_points = payload.get("plot_points")
    if isinstance(plot_points, list):
        points: list[str] = []
        for item in plot_points:
            if isinstance(item, str) and item.strip():
                points.append(_compact_text(item))
            elif isinstance(item, dict):
                desc = item.get("description")
                if isinstance(desc, str) and desc.strip():
                    points.append(_compact_text(desc))
        if points:
            return _compact_text("; ".join(points))[:max_chars]

    conflicts = payload.get("conflicts")
    if isinstance(conflicts, list):
        items: list[str] = []
        for item in conflicts:
            if isinstance(item, str) and item.strip():
                items.append(_compact_text(item))
            elif isinstance(item, dict):
                desc = item.get("description")
                if isinstance(desc, str) and desc.strip():
                    items.append(_compact_text(desc))
        if items:
            return _compact_text("; ".join(items))[:max_chars]

    title = payload.get("title")
    if isinstance(title, str):
        title = _compact_text(title)
        if title:
            return title[:max_chars]

    return None
