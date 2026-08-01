"""Stable generation-plan fingerprints shared by planning and resume gates."""

from .story_novel_length_contract import content_hash

_CHAPTER_KEYS = (
    "position",
    "title",
    "goal",
    "key_events",
    "character_focus",
    "open_threads",
    "end_state",
    "min_chars",
    "target_chars",
    "max_chars",
    "length_source",
    "preconditions",
    "required_event_ids",
    "state_transitions",
    "knowledge_grants",
    "location_transitions",
    "milestones_consumed",
    "forbidden_event_ids",
    "payoffs_due",
    "canon_refs",
    "timeline_event_bindings",
)
_INCREMENTAL_CHAPTER_KEYS = (
    "future_guard_entity_ids",
    "execution_contracts",
    "state_compiler",
    "contract_status",
    "entity_introductions",
    "effect_event_bindings",
    "effect_semantics",
    "effect_manifest",
    "contract_schema",
)

_V4_PLAN_KEYS = (
    "series_bible",
    "series_bible_hash",
    "series_roadmap",
    "series_roadmap_hash",
    "current_arc_plan",
    "current_arc_plan_hash",
    "arc_plans",
    "arc_plans_hash",
    "scope_graph",
    "scope_graph_hash",
    "world_reveal_index",
    "world_reveal_hash",
    "prompt_templates",
    "event_execution_contract_version",
    "prose_execution_boundary_version",
    "chapter_effect_manifest_version",
    "state_compiler_version",
    "frozen_through_position",
    "planner_snapshot_schema",
    "chapter_intent_schema",
    "chapter_contract_schema",
    "audit_proof_schema",
)


def generation_plan_hash(plan: dict) -> str:
    incremental = (
        plan.get("chapter_contract_mode") == "just_in_time"
        or plan.get("schema") == "story_novel_generation_plan.v4"
    )
    chapter_keys = (
        (*_CHAPTER_KEYS, *_INCREMENTAL_CHAPTER_KEYS) if incremental else _CHAPTER_KEYS
    )
    contract = {
        "schema": plan.get("schema"),
        "version": plan.get("version"),
        "story_seed_version": plan.get("story_seed_version"),
        "outline_hash": plan.get("outline_hash"),
        "canon_hash": plan.get("canon_hash"),
        "canon_gate_version": plan.get("canon_gate_version"),
        "thread_payoffs_hash": plan.get("thread_payoffs_hash"),
        "thread_payoffs_outline_hash": plan.get("thread_payoffs_outline_hash"),
        "model_policy": plan.get("model_policy"),
        "planning_contract_version": plan.get("planning_contract_version"),
        "future_guard_hash": plan.get("future_guard_hash"),
        "planning_invocations_hash": plan.get("planning_invocations_hash"),
        "length_profile": plan.get("length_profile"),
        "chapter_length_overrides": plan.get("chapter_length_overrides"),
        "chapters": [
            {key: row.get(key) for key in chapter_keys}
            for row in plan.get("chapters") or []
        ],
    }
    if incremental:
        contract.update(
            {
                "chapter_contract_mode": plan.get("chapter_contract_mode"),
                "incremental_planning_version": plan.get(
                    "incremental_planning_version"
                ),
                "compiled_chapter_count": plan.get("compiled_chapter_count"),
                "chapter_skeleton_hash": plan.get("chapter_skeleton_hash"),
            }
        )
        if "brief_policy_version" in plan:
            contract["brief_policy_version"] = plan["brief_policy_version"]
    if plan.get("schema") == "story_novel_generation_plan.v4":
        contract.update({key: plan.get(key) for key in _V4_PLAN_KEYS})
    return content_hash(contract)
