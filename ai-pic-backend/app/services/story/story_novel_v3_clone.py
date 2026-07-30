"""Reset chapter runtime evidence when cloning a v3 revision."""

from __future__ import annotations

import copy

from .story_novel_context_utils import CHAPTER_RUNTIME_FIELDS
from .story_novel_plan_versions import is_v3_plan


def clone_generation_plan(source: dict | None) -> dict:
    plan = copy.deepcopy(source or {})
    if not is_v3_plan(plan):
        return plan
    plan["chapters"] = [
        {
            key: value
            for key, value in row.items()
            if key not in CHAPTER_RUNTIME_FIELDS and key != "length_status"
        }
        for row in plan.get("chapters") or []
    ]
    return plan
