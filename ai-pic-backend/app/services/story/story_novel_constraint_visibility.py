"""Filter StorySeed policies that disclose future-only narrative details."""

from __future__ import annotations

import re

FUTURE_POLICY_MARKERS = (
    "提前",
    "未来章节",
    "后续章节",
    "终局",
    "结局",
)


def visible_content_constraints(
    snapshot: dict,
    canon: dict,
    visible_refs: set[str],
) -> tuple[list[str], int]:
    constraints = [
        str(item)
        for item in (snapshot.get("story_seed") or {}).get("content_constraints") or []
        if str(item).strip()
    ]
    hidden_names = {
        str(name)
        for entity in canon.get("entities") or []
        if entity.get("id") not in visible_refs
        for name in [entity.get("name"), *(entity.get("aliases") or [])]
        if name and len(str(name)) >= 2
    }
    visible = [
        item
        for item in constraints
        if not any(name in item for name in hidden_names)
        and not any(marker in item for marker in FUTURE_POLICY_MARKERS)
        and not re.search(r"第\s*\d+\s*章", item)
    ]
    return visible, len(constraints) - len(visible)
