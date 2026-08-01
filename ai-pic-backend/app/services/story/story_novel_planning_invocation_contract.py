"""Deterministic provenance rules for V3 planning invocation manifests."""

from __future__ import annotations

from .story_novel_context_utils import prompt_chapter_contract, value_hash


def entries_match_plan(plan: dict, entries: list[dict]) -> bool:
    stages = {str(item.get("logical_stage") or "") for item in entries}
    invocation_ids = [
        (item.get("attempt") or {}).get("invocation_id") for item in entries
    ]
    return bool(
        len(stages) == len(entries)
        and len(invocation_ids) == len(set(invocation_ids))
        and all(invocation_ids)
        and all(_entry_matches(plan, item) for item in entries)
        and all(_pair_complete(stage, stages) for stage in stages)
    )


def _entry_matches(plan: dict, entry: dict) -> bool:
    stage = str(entry.get("logical_stage") or "")
    prompt_template = (entry.get("attempt") or {}).get("prompt_template") or {}
    template = str(prompt_template.get("template") or "")
    expected_hash = _expected_result_hash(plan, stage, entry.get("positions") or [])
    return bool(
        template in _allowed_templates(stage)
        and _matches_frozen_policy(plan, prompt_template)
        and expected_hash
        and entry.get("result_hash") == expected_hash
    )


def _matches_frozen_policy(plan: dict, prompt_template: dict) -> bool:
    templates = (plan.get("prompt_templates") or {}).get("templates") or {}
    system_template = prompt_template.get("system_prompt") or {}
    return prompt_matches_frozen_policy(plan, prompt_template) and _same_source(
        system_template, templates.get("story_novel_system_v3") or {}
    )


def prompt_matches_frozen_policy(plan: dict, prompt_template: dict) -> bool:
    """Reject a planning call before it uses a drifted user prompt source."""
    templates = (plan.get("prompt_templates") or {}).get("templates") or {}
    frozen = templates.get(prompt_template.get("template")) or {}
    return _same_source(prompt_template, frozen)


def _same_source(actual: dict, frozen: dict) -> bool:
    fields = ("template", "resolved_template", "version", "sources_hash")
    return bool(frozen and all(actual.get(key) == frozen.get(key) for key in fields))


def _allowed_templates(stage: str) -> set[str]:
    if stage == "canon":
        return {"story_novel_canon_v3", "story_novel_canon_repair_v3"}
    if stage == "thread_schedule":
        return {"story_novel_thread_schedule_v3"}
    if stage == "thread_schedule.initial":
        return {"story_novel_thread_schedule_v3"}
    if stage == "thread_schedule.repair":
        return {"story_novel_thread_schedule_repair_v3"}
    if stage.startswith("chapter_plan.batch."):
        if stage.endswith(".repair"):
            return {
                "story_novel_plan_patch_repair_v3",
                "story_novel_plan_full_repair_v3",
            }
        return {"story_novel_plan_v3"}
    if stage.startswith("semantic_audit.batch."):
        return {"story_novel_plan_semantic_audit_v3"}
    if stage.startswith("chapter_package."):
        return {
            "story_novel_chapter_package_v3",
            "story_novel_chapter_intent_v4",
            "story_novel_format_repair_v3",
        }
    if stage.startswith("arc_plan."):
        return {"story_novel_arc_plan_v4", "story_novel_format_repair_v3"}
    return set()


def _expected_result_hash(plan: dict, stage: str, positions: list) -> str | None:
    if stage == "canon":
        return str(plan.get("canon_hash") or "") or None
    if stage.startswith("thread_schedule"):
        return value_hash(plan.get("thread_payoffs") or [])
    if stage.startswith(("chapter_plan.batch.", "semantic_audit.batch.")):
        covered = {int(item) for item in positions}
        rows = [
            prompt_chapter_contract(item)
            for item in plan.get("chapters") or []
            if int(item.get("position") or 0) in covered
        ]
        return value_hash(rows) if len(rows) == len(covered) else None
    if stage.startswith("chapter_package."):
        covered = {int(item) for item in positions}
        rows = [
            prompt_chapter_contract(item)
            for item in plan.get("chapters") or []
            if int(item.get("position") or 0) in covered
        ]
        return value_hash(rows) if len(rows) == len(covered) else None
    if stage.startswith("arc_plan."):
        arc_id = stage.split(".", 1)[1]
        return value_hash((plan.get("arc_plans") or {}).get(arc_id))
    return None


def _pair_complete(stage: str, stages: set[str]) -> bool:
    if stage.endswith(".initial"):
        base = stage.rsplit(".", 1)[0]
        suffix = ".verification" if base.startswith("semantic_audit.") else ".repair"
        return f"{base}{suffix}" in stages
    if stage.endswith((".repair", ".verification")):
        return f"{stage.rsplit('.', 1)[0]}.initial" in stages
    return True
