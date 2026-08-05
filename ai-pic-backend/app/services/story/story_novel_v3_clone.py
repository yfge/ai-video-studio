"""Reset chapter runtime evidence when cloning a v3 revision."""

from __future__ import annotations

import copy

from .story_novel_context_utils import CHAPTER_RUNTIME_FIELDS
from .story_novel_plan_versions import is_v3_plan, is_v4_plan, is_v5_plan
from .story_novel_v4_plan_reset import reset_v4_plan_from


def clone_generation_plan(source: dict | None) -> dict:
    plan = copy.deepcopy(source or {})
    if not (is_v3_plan(plan) or is_v4_plan(plan) or is_v5_plan(plan)):
        return plan
    if is_v5_plan(plan):
        plan["chapters"] = [
            {
                key: value
                for key, value in row.items()
                if key not in CHAPTER_RUNTIME_FIELDS
                and key
                not in {
                    "length_status",
                    "snapshot_before_hash",
                    "snapshot_after_hash",
                    "readability_status",
                }
            }
            for row in plan.get("chapters") or []
        ]
        return plan
    if is_v4_plan(plan):
        return reset_v4_plan_from(plan, 1)
    plan["chapters"] = [
        {
            key: value
            for key, value in row.items()
            if key not in CHAPTER_RUNTIME_FIELDS and key != "length_status"
        }
        for row in plan.get("chapters") or []
    ]
    return plan


def clone_ledger_schema(source: dict | None) -> str | None:
    if is_v5_plan(source):
        return "story_novel_continuity.v6"
    if is_v4_plan(source):
        return "story_novel_continuity.v5"
    if is_v3_plan(source):
        return "story_novel_continuity.v4"
    return None
