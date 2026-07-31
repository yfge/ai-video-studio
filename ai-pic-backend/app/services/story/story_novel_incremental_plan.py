"""Lightweight whole-book skeleton with just-in-time chapter contracts."""

from __future__ import annotations

import copy

from app.schemas.story_novel_longform import StoryNovelChapterPlan
from pydantic import ValidationError

from .story_novel_brief_policy import BRIEF_POLICY_VERSION
from .story_novel_chapter_effect_manifest import VERSION as EFFECT_MANIFEST_VERSION
from .story_novel_chapter_effect_manifest import effect_manifest_checkpoint_valid
from .story_novel_context_utils import CHAPTER_RUNTIME_FIELDS, value_hash
from .story_novel_entity_mentions import visible_entity_ids
from .story_novel_future_guard_index import (
    compile_future_guard_index,
    future_guard_index_matches,
)
from .story_novel_plan_execution_contract import execution_contracts_valid
from .story_novel_plan_state_compiler import STATE_COMPILER_VERSION
from .story_novel_planning_batches import validated_prefix_context
from .story_novel_planning_invocations import valid as valid_planning_invocations
from .story_novel_prompt_renderer import (
    v3_prompt_template_policy,
    valid_v3_prompt_template_policy,
)
from .story_novel_prose_context import PROSE_EXECUTION_BOUNDARY_VERSION
from .story_novel_thread_schedule import payoffs_by_position
from .story_novel_timeline_contract import compile_timeline_bindings
from .story_novel_world_expansion import canon_with_plan_expansion
from .story_novel_world_reveal import (
    compile_world_reveal_index,
    world_reveal_index_matches,
)

MODE = "just_in_time"
VERSION = 1
PLANNING_CONTRACT_VERSION = 9

_OUTLINE_KEYS = (
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
    "length",
)
_SKELETON_KEYS = (*_OUTLINE_KEYS, "required_event_ids", "timeline_event_bindings")


def is_incremental_plan(plan: dict | None) -> bool:
    return (plan or {}).get("chapter_contract_mode") == MODE


def build_chapter_skeletons(
    canon: dict, frozen_spec: dict, thread_payoffs: list[dict] | None
) -> list[dict]:
    scheduled = payoffs_by_position(thread_payoffs or [])
    milestones: dict[int, list[str]] = {}
    for item in canon.get("milestones") or []:
        position = item.get("planned_position")
        if position is not None:
            milestones.setdefault(int(position), []).append(str(item["id"]))
    rows = []
    prior_events: list[str] = []
    for source in frozen_spec.get("chapters") or []:
        position = int(source["position"])
        events = [
            f"event-{position}-{index}"
            for index, _ in enumerate(source.get("key_events") or [], start=1)
        ]
        entity_ids = visible_entity_ids(canon, source, _OUTLINE_KEYS)
        row = {
            **{
                key: copy.deepcopy(source[key])
                for key in _OUTLINE_KEYS
                if key in source
            },
            "required_event_ids": events,
            "preconditions": [],
            "state_transitions": [],
            "knowledge_grants": [],
            "location_transitions": [],
            "milestones_consumed": milestones.get(position, []),
            "forbidden_event_ids": list(prior_events),
            "payoffs_due": list(scheduled.get(position, [])),
            "canon_refs": [*entity_ids, *milestones.get(position, [])],
            "future_guard_entity_ids": entity_ids,
            "execution_contracts": [],
            "contract_status": "pending",
        }
        rows.append(row)
        prior_events.extend(events)
    rows = compile_timeline_bindings(canon, rows)
    _require_contiguous(rows)
    return rows


def incremental_plan_fields(canon: dict, chapters: list[dict]) -> dict:
    future = compile_future_guard_index(
        chapters,
        milestones=canon.get("milestones") or [],
        entities=canon.get("entities") or [],
    )
    reveal = compile_world_reveal_index(canon, chapters)
    return {
        "chapter_contract_mode": MODE,
        "incremental_planning_version": VERSION,
        "planning_contract_version": PLANNING_CONTRACT_VERSION,
        "event_execution_contract_version": 1,
        "prose_execution_boundary_version": PROSE_EXECUTION_BOUNDARY_VERSION,
        "chapter_effect_manifest_version": EFFECT_MANIFEST_VERSION,
        "state_compiler_version": STATE_COMPILER_VERSION,
        "brief_policy_version": BRIEF_POLICY_VERSION,
        "compiled_chapter_count": 0,
        "chapter_skeleton_hash": skeleton_hash(chapters),
        "future_guard_index": future,
        "future_guard_hash": future["index_hash"],
        "world_reveal_index": reveal,
        "world_reveal_hash": reveal["index_hash"],
        "prompt_templates": v3_prompt_template_policy(version=9),
    }


def skeleton_hash(chapters: list[dict]) -> str:
    return value_hash([chapter_skeleton(item) for item in chapters])


def chapter_skeleton(chapter: dict) -> dict:
    result = {key: copy.deepcopy(chapter.get(key)) for key in _SKELETON_KEYS}
    for key in (
        "milestones_consumed",
        "forbidden_event_ids",
        "payoffs_due",
        "canon_refs",
        "future_guard_entity_ids",
    ):
        result[key] = copy.deepcopy(chapter.get(key) or [])
    return result


def compiled_count(plan: dict) -> int:
    return int(plan.get("compiled_chapter_count") or 0)


def valid_incremental_plan(plan: dict) -> bool:
    if not is_incremental_plan(plan):
        return False
    chapters = list(plan.get("chapters") or [])
    count = compiled_count(plan)
    try:
        _require_contiguous(chapters)
        if not 0 <= count <= len(chapters):
            return False
        if plan.get("chapter_skeleton_hash") != skeleton_hash(chapters):
            return False
        canon = plan.get("canon") or {}
        expected = compile_future_guard_index(
            chapters,
            milestones=canon.get("milestones") or [],
            entities=canon.get("entities") or [],
        )
        index = plan.get("future_guard_index") or {}
        if not future_guard_index_matches(index, expected):
            return False
        reveal = compile_world_reveal_index(canon, chapters)
        if not world_reveal_index_matches(plan.get("world_reveal_index") or {}, reveal):
            return False
        for index_value, row in enumerate(chapters):
            expected_status = "compiled" if index_value < count else "pending"
            if row.get("contract_status") != expected_status:
                return False
        compiled = chapters[:count]
        for row in compiled:
            StoryNovelChapterPlan.model_validate(row)
            if not execution_contracts_valid(row):
                return False
            if not effect_manifest_checkpoint_valid(row):
                return False
            if (
                int((row.get("state_compiler") or {}).get("version") or 0)
                != STATE_COMPILER_VERSION
            ):
                return False
        if compiled:
            validated_prefix_context(
                canon_with_plan_expansion(canon, compiled), compiled
            )
    except (KeyError, TypeError, ValueError, ValidationError):
        return False
    return bool(
        int(plan.get("incremental_planning_version") or 0) == VERSION
        and int(plan.get("planning_contract_version") or 0) == PLANNING_CONTRACT_VERSION
        and int(plan.get("event_execution_contract_version") or 0) == 1
        and int(plan.get("prose_execution_boundary_version") or 0)
        == PROSE_EXECUTION_BOUNDARY_VERSION
        and int(plan.get("chapter_effect_manifest_version") or 0)
        == EFFECT_MANIFEST_VERSION
        and int(plan.get("state_compiler_version") or 0) == STATE_COMPILER_VERSION
        and plan.get("future_guard_hash") == index.get("index_hash")
        and plan.get("world_reveal_hash")
        == (plan.get("world_reveal_index") or {}).get("index_hash")
        and isinstance(plan.get("model_policy"), dict)
        and valid_v3_prompt_template_policy(plan.get("prompt_templates") or {})
        and valid_planning_invocations(plan)
    )


def strip_runtime(row: dict) -> dict:
    return {
        key: value for key, value in row.items() if key not in CHAPTER_RUNTIME_FIELDS
    }


def _require_contiguous(chapters: list[dict]) -> None:
    positions = [int(item.get("position") or 0) for item in chapters]
    if positions != list(range(1, len(chapters) + 1)):
        raise ValueError("轻量章节骨架必须从 1 连续编号")
    if any(
        len(item.get("required_event_ids") or []) != len(item.get("key_events") or [])
        for item in chapters
    ):
        raise ValueError("轻量章节骨架事件 ID 与 key_events 不一一对应")
