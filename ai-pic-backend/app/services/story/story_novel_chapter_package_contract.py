from __future__ import annotations

import copy
import json

from app.schemas.story_novel_longform import StoryNovelEventExecution

from . import story_novel_chapter_package_normalization as normalization
from .story_novel_brief_location_scope import brief_allowed_entity_ids
from .story_novel_chapter_brief_contract import validate_model_brief
from .story_novel_chapter_effect_manifest import compile_effect_manifest
from .story_novel_chapter_package_context import build_final_package_context
from .story_novel_chapter_package_recovery import extract_chapter_package_payload
from .story_novel_incremental_plan import chapter_skeleton
from .story_novel_plan_effect_refs import chapter_actor_refs
from .story_novel_plan_parser import parse_plan
from .story_novel_planning_batches import batch_frozen_spec, batch_thread_payoffs
from .story_novel_world_expansion import (
    canon_with_plan_expansion,
    normalize_package_expansion,
)

_normalize_missing_contract_fields = normalization.normalize_missing_contract_fields
_strip_thread_state_transitions = normalization.strip_invalid_model_fields


def parse_chapter_package(
    text, service, revision, position: int, *, package_input=None
):
    payload = extract_chapter_package_payload(text)
    if not isinstance(payload, dict) or set(payload) != {
        "chapter_contract",
        "chapter_brief",
    }:
        raise ValueError("package 必须且只含 chapter_contract/chapter_brief")
    plan = dict(revision.generation_plan or {})
    skeleton = _row(plan, position)
    state_before = (package_input or {}).get("state_before") or {}
    model_contract, model_brief = normalize_package_expansion(
        _freeze_skeleton(payload["chapter_contract"], skeleton),
        payload["chapter_brief"],
        plan.get("canon") or {},
        state_before,
    )
    validation_canon = canon_with_plan_expansion(
        plan.get("canon") or {},
        [*list(plan.get("chapters") or [])[: position - 1], model_contract],
        state_before,
    )
    model_contract = normalization.normalize_missing_contract_fields(
        model_contract,
        validation_canon,
        state_before=state_before,
    )
    raw_contract = normalization.strip_invalid_model_fields(
        model_contract, state_before=(package_input or {}).get("state_before")
    )
    repair_issues = normalization.repairable_contract_issues(raw_contract)
    if repair_issues:
        detail = "; ".join(repair_issues)
        raise ValueError(f"chapter package typed 字段遗漏，仅补字段不改语义: {detail}")
    prior = list(plan.get("chapters") or [])[: position - 1]
    parsed, error = parse_plan(
        json.dumps({"chapters": [raw_contract]}, ensure_ascii=False),
        [position],
        validation_canon,
        batch_frozen_spec(plan, [position]),
        batch_thread_payoffs(plan.get("thread_payoffs") or [], [position]),
        prior_chapters=prior,
        require_complete=position == len(plan.get("chapters") or []),
    )
    if not parsed:
        raise ValueError(error or "当前章节合同无效")
    contract = _finalize_contract(
        parsed["chapters"][0],
        skeleton,
        validation_canon,
    )
    context = build_final_package_context(
        service, revision, position, contract, model_brief
    )
    brief = _bound_brief(model_brief, context["brief_input"])
    return contract, brief, context


def _freeze_skeleton(raw, skeleton: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("chapter_contract 必须是对象")
    result = copy.deepcopy(raw)
    for key, value in chapter_skeleton(skeleton).items():
        result[key] = copy.deepcopy(value)
    return result


def _finalize_contract(
    row: dict,
    skeleton: dict,
    canon: dict,
) -> dict:
    result = copy.deepcopy(row)
    for key, value in chapter_skeleton(skeleton).items():
        result[key] = copy.deepcopy(value)
    required = list(result.get("required_event_ids") or [])
    executions = list(result.get("execution_contracts") or [])
    if [
        item.get("event_id") for item in executions if isinstance(item, dict)
    ] != required:
        raise ValueError("chapter package execution_contracts 未逐项覆盖当前事件")
    allowed = chapter_actor_refs(result, canon.get("entities") or [])
    bindings = result.get("timeline_event_bindings") or {}
    grants = result.get("knowledge_grants") or []
    normalized = []
    for raw in executions:
        item = StoryNovelEventExecution.model_validate(raw).model_dump()
        event_id = item["event_id"]
        item["actor_ids"] = [value for value in item["actor_ids"] if value in allowed]
        item["timeline_ids"] = [
            key for key, value in bindings.items() if value == event_id
        ]
        item["knowledge_fact_ids"] = list(
            dict.fromkeys(
                grant["fact_id"]
                for grant in grants
                if grant.get("source_event_id") == event_id
            )
        )
        normalized.append(item)
    result.update(
        execution_contracts=normalized,
        contract_status="compiled",
        future_guard_entity_ids=list(skeleton.get("future_guard_entity_ids") or []),
    )
    result["effect_manifest"] = compile_effect_manifest(result, canon)
    return result


def _bound_brief(raw, brief_input: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("chapter_brief 必须是对象")
    beats = list(raw.get("beats") or [])
    count = int(brief_input["expected_beat_count"])
    if len(beats) != count or any(not isinstance(item, dict) for item in beats):
        raise ValueError(f"chapter brief 必须包含 {count} 个 beats")
    contract = brief_input["chapter_contract"]
    event_ids = list(contract.get("required_event_ids") or [])
    beats = _bind_events(beats, event_ids)
    effect_ids = [
        item["contract_id"] for item in brief_input["expected_delta"]["proof_contracts"]
    ]
    _bind_effects(beats, effect_ids, brief_input["expected_delta"])
    budgets = _budgets(beats, int(contract["target_chars"]))
    allowed = brief_allowed_entity_ids(brief_input)
    normalized = []
    for index, beat in enumerate(beats, start=1):
        normalized.append(
            {
                "beat_id": f"B{index:02d}",
                "purpose": beat.get("purpose"),
                "target_chars": budgets[index - 1],
                "allowed_entity_ids": allowed,
                "bound_event_ids": beat["bound_event_ids"],
                "effect_contract_ids": beat["effect_contract_ids"],
            }
        )
    result = {
        "schema": "story_novel_chapter_brief.v1",
        "chapter_contract_hash": brief_input["chapter_contract_hash"],
        "state_before_hash": brief_input["state_before_hash"],
        "input_evidence_hash": brief_input["input_evidence_hash"],
        "execution_contracts": list(contract.get("execution_contracts") or []),
        "beats": normalized,
        "character_motivations": _motivations(raw, set(allowed)),
        "emotional_continuity": raw.get("emotional_continuity"),
        "causal_bridge": raw.get("causal_bridge"),
        "summary": raw.get("summary"),
        "cliffhanger": raw.get("cliffhanger"),
        "continuity_watchpoints": raw.get("continuity_watchpoints") or [],
        "setup_thread_ids": list(contract.get("open_threads") or []),
        "payoff_thread_ids": list(contract.get("payoffs_due") or []),
    }
    return validate_model_brief(result, brief_input)


def _bind_events(beats: list[dict], event_ids: list[str]) -> list[dict]:
    allowed = set(event_ids)
    for beat in beats:
        beat["bound_event_ids"] = list(
            dict.fromkeys(
                value for value in beat.get("bound_event_ids") or [] if value in allowed
            )
        )
        beat["effect_contract_ids"] = []
    covered = {value for beat in beats for value in beat["bound_event_ids"]}
    for index, event_id in enumerate(
        value for value in event_ids if value not in covered
    ):
        beats[min(index, len(beats) - 1)]["bound_event_ids"].append(event_id)
    return beats


def _bind_effects(beats: list[dict], effect_ids: list[str], delta: dict) -> None:
    event_by_effect = {f"event:{value}": value for value in delta["occurred_event_ids"]}
    event_by_effect.update(
        {
            f"knowledge:{index}": grant["source_event_id"]
            for index, grant in enumerate(delta["knowledge_grants"], start=1)
        }
    )
    event_by_effect.update(
        {
            f"entity:{item['id']}": item["source_event_id"]
            for item in delta.get("entity_introductions") or []
        }
    )
    for effect_id in effect_ids:
        event_id = event_by_effect.get(effect_id)
        target = next(
            (beat for beat in beats if event_id in beat["bound_event_ids"]), beats[-1]
        )
        target["effect_contract_ids"].append(effect_id)


def _budgets(beats: list[dict], target: int) -> list[int]:
    supplied = [item.get("target_chars") for item in beats]
    if (
        all(type(value) is int and value > 0 for value in supplied)
        and sum(supplied) == target
    ):
        return supplied
    base, extra = divmod(target, len(beats))
    return [base + int(index < extra) for index in range(len(beats))]


def _motivations(raw: dict, allowed: set[str]) -> list[dict]:
    return [
        item
        for item in raw.get("character_motivations") or []
        if isinstance(item, dict)
        and set(item) == {"character_id", "motivation"}
        and item.get("character_id") in allowed
    ]


def _row(plan: dict, position: int) -> dict:
    rows = plan.get("chapters") or []
    return next(item for item in rows if int(item["position"]) == position)
