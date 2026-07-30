"""Generation-plan v3 finalization fields."""

from .story_novel_future_guard_index import (
    compile_future_guard_index,
    future_guard_index_matches,
)
from .story_novel_incremental_plan import is_incremental_plan, valid_incremental_plan
from .story_novel_plan_execution_contract import execution_contracts_valid
from .story_novel_plan_state_compiler import STATE_COMPILER_VERSION
from .story_novel_plan_versions import V2_SCHEMA, V3_SCHEMA
from .story_novel_planning_invocations import valid as valid_planning_invocations
from .story_novel_prompt_renderer import (
    v3_prompt_template_policy,
    valid_v3_prompt_template_policy,
)


def plan_schema(revision, frozen_spec) -> str:
    return (frozen_spec or revision.generation_plan or {}).get("schema") or V2_SCHEMA


def v3_plan_fields(schema: str, canon: dict, chapters: list[dict]) -> dict:
    if schema != V3_SCHEMA:
        return {}
    if not all(execution_contracts_valid(item) for item in chapters):
        raise ValueError("v3 章节计划缺少完整 event execution contract")
    future_index = compile_future_guard_index(
        chapters,
        milestones=canon.get("milestones") or [],
        entities=canon.get("entities") or [],
    )
    return {
        "planning_contract_version": 3,
        "event_execution_contract_version": 1,
        "state_compiler_version": STATE_COMPILER_VERSION,
        "future_guard_index": future_index,
        "future_guard_hash": future_index["index_hash"],
        "prompt_templates": v3_prompt_template_policy(),
    }


def valid_v3_plan_fields(plan: dict) -> bool:
    if plan.get("schema") != V3_SCHEMA:
        return True
    if is_incremental_plan(plan):
        return valid_incremental_plan(plan)
    try:
        index = dict(plan.get("future_guard_index") or {})
        stored = index.get("index_hash")
        canon = plan.get("canon") or {}
        expected = compile_future_guard_index(
            plan.get("chapters") or [],
            milestones=canon.get("milestones") or [],
            entities=canon.get("entities") or [],
        )
    except (KeyError, TypeError, ValueError):
        return False
    return bool(
        int(plan.get("planning_contract_version") or 0) == 3
        and int(plan.get("event_execution_contract_version") or 0) == 1
        and int(plan.get("state_compiler_version") or 0) == STATE_COMPILER_VERSION
        and all(
            int((item.get("state_compiler") or {}).get("version") or 0)
            == STATE_COMPILER_VERSION
            for item in plan.get("chapters") or []
        )
        and all(execution_contracts_valid(item) for item in plan.get("chapters") or [])
        and stored
        and plan.get("future_guard_hash") == stored
        and future_guard_index_matches(index, expected)
        and isinstance(plan.get("model_policy"), dict)
        and valid_v3_prompt_template_policy(plan.get("prompt_templates") or {})
        and valid_planning_invocations(plan)
    )
