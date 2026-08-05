from __future__ import annotations

import copy

from .story_novel_brief_location_scope import (
    normalize_model_brief,
    validate_brief_location_scope,
)
from .story_novel_brief_policy import LEGACY_BRIEF_POLICY_VERSION, expected_beat_count
from .story_novel_context_utils import value_hash
from .story_novel_continuity_watchpoints import validate_continuity_watchpoints
from .story_novel_expected_delta import compile_expected_delta

BRIEF_INPUT_SCHEMA = "story_novel_chapter_brief_input.v1"
BRIEF_SCHEMA = "story_novel_chapter_brief.v1"
_MODEL_KEYS = {
    "schema",
    "chapter_contract_hash",
    "state_before_hash",
    "input_evidence_hash",
    "execution_contracts",
    "beats",
    "character_motivations",
    "emotional_continuity",
    "causal_bridge",
    "summary",
    "cliffhanger",
    "continuity_watchpoints",
    "setup_thread_ids",
    "payoff_thread_ids",
    "brief_hash",
}


def compile_chapter_brief_input(
    chapter_contract: dict,
    state_before: dict,
    world_events=(),
    character_memories=(),
    allowed_entity_ids=(),
    brief_policy_version: str = LEGACY_BRIEF_POLICY_VERSION,
) -> dict:
    if not isinstance(chapter_contract, dict) or not isinstance(state_before, dict):
        raise ValueError("chapter_contract 和 state_before 必须是对象")
    target_chars = chapter_contract.get("target_chars")
    evidence = {
        "world_events": _evidence_rows(world_events, "world_event"),
        "character_memories": _evidence_rows(character_memories, "character_memory"),
    }
    entity_ids = _unique_ids(allowed_entity_ids, "allowed_entity_ids")
    expected_delta = compile_expected_delta(chapter_contract, state_before)
    return {
        "schema": BRIEF_INPUT_SCHEMA,
        "chapter_contract": copy.deepcopy(chapter_contract),
        "chapter_contract_hash": value_hash(chapter_contract),
        "state_before": copy.deepcopy(state_before),
        "state_before_hash": value_hash(state_before),
        "planning_evidence": evidence,
        "brief_policy_version": brief_policy_version,
        "input_evidence_hash": value_hash(
            {"brief_policy_version": brief_policy_version, "evidence": evidence}
        ),
        "allowed_entity_ids": entity_ids,
        "expected_beat_count": expected_beat_count(target_chars, brief_policy_version),
        "expected_delta": expected_delta,
    }


def validate_chapter_brief(
    brief: dict,
    brief_input: dict,
    *,
    enforce_location_scope: bool = False,
    normalize_model_aliases: bool = False,
) -> dict:
    if normalize_model_aliases:
        brief = normalize_model_brief(
            brief, set(brief_input.get("allowed_entity_ids") or [])
        )
    if brief_input.get("schema") != BRIEF_INPUT_SCHEMA:
        raise ValueError("chapter brief input schema 无效")
    if not isinstance(brief, dict) or brief.get("schema") != BRIEF_SCHEMA:
        raise ValueError("chapter brief schema 无效")
    unexpected = set(brief).difference(_MODEL_KEYS)
    if unexpected:
        raise ValueError(f"chapter brief 包含越界字段: {sorted(unexpected)}")
    _require_binding(brief, brief_input, "chapter_contract_hash")
    _require_binding(brief, brief_input, "state_before_hash")
    _require_binding(brief, brief_input, "input_evidence_hash")

    beats = list(brief.get("beats") or [])
    count = int(brief_input["expected_beat_count"])
    if len(beats) != count:
        raise ValueError(f"chapter brief 必须包含 {count} 个 beats")
    if any(not isinstance(item, dict) for item in beats):
        raise ValueError("beat 必须是对象")
    expected_ids = [f"B{index:02d}" for index in range(1, count + 1)]
    if [item.get("beat_id") for item in beats] != expected_ids:
        raise ValueError("beat ID 必须从 B01 连续编号")

    allowed_entities = set(brief_input.get("allowed_entity_ids") or [])
    contract = brief_input["chapter_contract"]
    if brief.get("execution_contracts") != list(
        contract.get("execution_contracts") or []
    ):
        raise ValueError("chapter brief execution_contracts 必须逐字复制章节合同")
    allowed_events = set(contract.get("required_event_ids") or [])
    allowed_effects = {
        item["contract_id"] for item in brief_input["expected_delta"]["proof_contracts"]
    }
    for beat in beats:
        _validate_beat(beat, allowed_entities, allowed_events, allowed_effects)
    if enforce_location_scope:
        validate_brief_location_scope(beats, brief_input)
    target_chars = int(contract["target_chars"])
    if sum(item["target_chars"] for item in beats) != target_chars:
        raise ValueError("beat 字符预算之和必须等于章节 target_chars")

    _validate_motivations(brief, allowed_entities)
    watchpoints = validate_continuity_watchpoints(
        brief.get("continuity_watchpoints"), brief_input
    )
    for key in ("emotional_continuity", "causal_bridge", "summary", "cliffhanger"):
        _require_text(brief, key)
    _require_complete_coverage(beats, "bound_event_ids", allowed_events, "当前章节事件")
    _require_complete_coverage(
        beats, "effect_contract_ids", allowed_effects, "expected delta"
    )
    _require_exact_ids(brief, "setup_thread_ids", contract.get("open_threads") or [])
    _require_exact_ids(brief, "payoff_thread_ids", contract.get("payoffs_due") or [])
    result = copy.deepcopy(brief)
    if "continuity_watchpoints" in result:
        result["continuity_watchpoints"] = watchpoints
    stored_hash = result.pop("brief_hash", None)
    calculated_hash = value_hash(result)
    if stored_hash is not None and stored_hash != calculated_hash:
        raise ValueError("chapter brief hash 不匹配")
    result["brief_hash"] = calculated_hash
    return result


def validate_model_brief(brief: dict, source: dict) -> dict:
    return validate_chapter_brief(
        brief, source, enforce_location_scope=True, normalize_model_aliases=True
    )


def _validate_beat(
    beat: dict, allowed_entities: set, allowed_events: set, allowed_effects: set
) -> None:
    allowed_keys = {
        "beat_id",
        "purpose",
        "target_chars",
        "allowed_entity_ids",
        "bound_event_ids",
        "effect_contract_ids",
    }
    if not isinstance(beat, dict) or set(beat).difference(allowed_keys):
        raise ValueError("beat 包含越界字段")
    if not isinstance(beat.get("purpose"), str) or not beat["purpose"].strip():
        raise ValueError("beat purpose 不能为空")
    if isinstance(beat.get("target_chars"), bool) or not isinstance(
        beat.get("target_chars"), int
    ):
        raise ValueError("beat target_chars 必须是正整数")
    if beat["target_chars"] <= 0:
        raise ValueError("beat target_chars 必须是正整数")
    _subset(beat.get("allowed_entity_ids"), allowed_entities, "实体")
    _subset(beat.get("bound_event_ids"), allowed_events, "事件")
    _subset(beat.get("effect_contract_ids"), allowed_effects, "effect contract")


def _validate_motivations(brief: dict, allowed_entities: set) -> None:
    for item in brief.get("character_motivations") or []:
        if set(item) != {"character_id", "motivation"}:
            raise ValueError("character motivation 结构无效")
        if item["character_id"] not in allowed_entities:
            raise ValueError("character motivation 引用了越界实体")
        if not isinstance(item["motivation"], str) or not item["motivation"].strip():
            raise ValueError("character motivation 不能为空")


def _evidence_rows(values, kind: str) -> list[dict]:
    rows = []
    for value in values or []:
        if not isinstance(value, dict):
            raise ValueError("planning evidence 必须是对象")
        item = copy.deepcopy(value)
        item_id = item.get("id") or item.get("business_id")
        source_hash = item.get("source_hash")
        if not item_id or not source_hash:
            raise ValueError("planning evidence 缺少 id/source_hash")
        item["evidence_kind"] = kind
        item["evidence_id"] = str(item_id)
        rows.append(item)
    keys = [(item["evidence_kind"], item["evidence_id"]) for item in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("planning evidence ID 重复")
    return rows


def _require_binding(brief: dict, source: dict, key: str) -> None:
    if brief.get(key) != source.get(key):
        raise ValueError(f"chapter brief {key} 不匹配")


def _require_text(value: dict, key: str) -> None:
    if not isinstance(value.get(key), str) or not value[key].strip():
        raise ValueError(f"chapter brief {key} 不能为空")


def _require_exact_ids(brief: dict, key: str, expected) -> None:
    rows = _unique_ids(brief.get(key) or (), key)
    if rows != list(expected):
        raise ValueError(f"chapter brief {key} 必须完整覆盖当前章节合同")


def _require_complete_coverage(beats, key: str, expected: set, label: str) -> None:
    supplied = {value for beat in beats for value in beat.get(key) or []}
    if supplied != expected:
        missing = sorted(expected.difference(supplied))
        unexpected = sorted(supplied.difference(expected))
        raise ValueError(
            f"chapter brief 必须完整覆盖{label}; "
            f"缺少 ID: {missing}; 多余 ID: {unexpected}"
        )


def _subset(values, allowed: set, label: str) -> None:
    rows = _unique_ids(values or (), label)
    invalid = set(rows).difference(allowed)
    if invalid:
        raise ValueError(f"{label} 引用了当前章节合同外 ID: {sorted(invalid)}")


def _unique_ids(values, label: str) -> list[str]:
    rows = list(values or [])
    if any(not isinstance(item, str) or not item.strip() for item in rows):
        raise ValueError(f"{label} 必须是非空字符串 ID")
    if len(rows) != len(set(rows)):
        raise ValueError(f"{label} ID 重复")
    return rows
