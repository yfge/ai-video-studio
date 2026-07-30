"""Explicit event-by-event review of persistent effects in chapter packages."""

from __future__ import annotations

from . import story_novel_effect_source_binding as effect_binding
from .story_novel_context_utils import value_hash

VERSION = 1
_ROW_KEYS = {"event_id", "field_reviews", "no_persistent_effect", "rationale"}
_FIELD_KEYS = {"subject_id", "field", "disposition", "effect_refs", "reason"}


def build_effect_review_contracts(
    skeleton: dict, canon: dict, state_before: dict
) -> list[dict]:
    entities = {str(item["id"]): item for item in canon.get("entities") or []}
    subjects = state_before.get("subjects") or {}
    events = list(skeleton.get("key_events") or [])
    event_ids = list(skeleton.get("required_event_ids") or [])
    if len(events) != len(event_ids):
        raise ValueError("effect review 的事件 ID 与 key_events 未一一对应")
    result = []
    for event_id, event in zip(event_ids, events, strict=True):
        mentioned = {
            subject_id
            for subject_id, entity in entities.items()
            if any(
                str(name) in str(event)
                for name in [entity.get("name"), *(entity.get("aliases") or [])]
                if str(name or "").strip()
            )
        }
        result.append(
            {
                "event_id": event_id,
                "required_field_reviews": [
                    {"subject_id": subject_id, "field": field}
                    for subject_id in sorted(mentioned)
                    for field in sorted((subjects.get(subject_id) or {}).keys())
                    if field != "possessions"
                ],
            }
        )
    return result


def validate_effect_coverage(
    raw,
    contract: dict,
    review_contracts: list[dict],
    canon: dict,
    *,
    stale_effect_refs: set[str] | None = None,
) -> dict:
    rows = list(raw or [])
    event_ids = list(contract.get("required_event_ids") or [])
    if [item.get("event_id") for item in rows if isinstance(item, dict)] != event_ids:
        raise ValueError("effect_coverage 必须按顺序逐项覆盖 required_event_ids")
    required = {
        item["event_id"]: {
            (row["subject_id"], row["field"])
            for row in item.get("required_field_reviews") or []
        }
        for item in review_contracts
    }
    effects = effect_catalog(contract, canon)
    rows = effect_binding.normalize_top_level_effect_refs(rows, effects)
    rows = _complete_equivalent_refs(rows, effects)
    claimed = set()
    normalized = []
    for item in rows:
        if set(item) != _ROW_KEYS:
            raise ValueError("effect_coverage 项字段无效")
        event_id = item["event_id"]
        reviews = _validate_field_reviews(
            item.get("field_reviews"),
            event_id,
            required.get(event_id, set()),
            effects,
            stale_effect_refs or set(),
        )
        refs = {ref for review in reviews for ref in review["effect_refs"]}
        if claimed.intersection(refs):
            raise ValueError("effect_coverage 的 typed effect 被多个事件重复认领")
        claimed.update(refs)
        no_effect = item.get("no_persistent_effect")
        if type(no_effect) is not bool:
            raise ValueError("no_persistent_effect 必须是 bool")
        no_effect = not bool(refs)
        rationale = str(item.get("rationale") or "").strip()
        if not rationale:
            raise ValueError("effect_coverage.rationale 不能为空")
        normalized.append(
            {
                "event_id": event_id,
                "field_reviews": reviews,
                "no_persistent_effect": no_effect,
                "rationale": rationale,
            }
        )
    missing = set(effects).difference(claimed)
    if missing:
        raise ValueError(f"effect_coverage 未绑定 typed effects: {sorted(missing)}")
    payload = {"version": VERSION, "items": normalized}
    payload["coverage_hash"] = value_hash(payload)
    return payload


def coverage_checkpoint_valid(chapter: dict) -> bool:
    coverage = chapter.get("effect_coverage") or {}
    if int(coverage.get("version") or 0) != VERSION:
        return False
    candidate = {"version": VERSION, "items": coverage.get("items") or []}
    return coverage.get("coverage_hash") == value_hash(candidate) and [
        item.get("event_id") for item in candidate["items"]
    ] == list(chapter.get("required_event_ids") or [])


def _validate_field_reviews(raw, event_id, required, effects, stale_refs) -> list[dict]:
    rows = list(raw or [])
    pairs = []
    normalized = []
    for item in rows:
        if not isinstance(item, dict) or set(item) != _FIELD_KEYS:
            raise ValueError("effect_coverage.field_reviews 字段无效")
        pair = (str(item.get("subject_id") or ""), str(item.get("field") or ""))
        if not all(pair) or pair in pairs:
            raise ValueError("effect_coverage.field_reviews subject/field 缺失或重复")
        pairs.append(pair)
        raw_refs = list(
            dict.fromkeys(str(value) for value in item.get("effect_refs") or [])
        )
        if any(ref not in effects and ref not in stale_refs for ref in raw_refs):
            raise ValueError(
                "effect_coverage.field_reviews 引用了不匹配的 typed effect"
            )
        refs = [ref for ref in raw_refs if ref in effects]
        if any(effects[ref][0] != pair for ref in refs):
            raise ValueError(
                "effect_coverage.field_reviews 引用了不匹配的 typed effect"
            )
        if any(effects[ref][1] not in {None, event_id} for ref in refs):
            raise ValueError("effect_coverage 将 effect 绑定到错误事件")
        if item.get("disposition") not in {"changed", "unchanged"}:
            raise ValueError("effect_coverage disposition 必须为 changed/unchanged")
        disposition = "changed" if refs else "unchanged"
        reason = str(item.get("reason") or "").strip()
        if not reason:
            raise ValueError("effect_coverage field review reason 不能为空")
        normalized.append(
            {
                "subject_id": pair[0],
                "field": pair[1],
                "disposition": disposition,
                "effect_refs": refs,
                "reason": reason,
            }
        )
    missing = required.difference(pairs)
    if missing:
        raise ValueError(
            f"effect_coverage 未审查当前事件涉及的状态字段: {sorted(missing)}"
        )
    return normalized


def effect_catalog(
    contract: dict, canon: dict
) -> dict[str, tuple[tuple, str | None, dict]]:
    result = {}
    for index, item in enumerate(contract.get("state_transitions") or [], 1):
        result[f"state:{index}"] = (
            (item.get("subject_id"), item.get("field")),
            None,
            {"operator": "eq", "value": item.get("to_value")},
        )
    for index, item in enumerate(contract.get("location_transitions") or [], 1):
        result[f"location:{index}"] = (
            (item.get("subject_id"), "location"),
            None,
            {"operator": "eq", "value": item.get("to_location_id")},
        )
    for index, item in enumerate(contract.get("knowledge_grants") or [], 1):
        result[f"knowledge:{index}"] = (
            (item.get("character_id"), "knowledge"),
            item.get("source_event_id"),
            {"operator": "contains", "value": item.get("fact_id")},
        )
    milestones = {item.get("id"): item for item in canon.get("milestones") or []}
    for milestone_id in contract.get("milestones_consumed") or []:
        for outcome in (milestones.get(milestone_id) or {}).get("outcomes") or []:
            result[
                f"milestone:{milestone_id}:{outcome['subject_id']}:{outcome['field']}"
            ] = (
                (outcome["subject_id"], outcome["field"]),
                None,
                {"operator": outcome["operator"], "value": outcome.get("value")},
            )
    return result


def stale_effect_refs(raw_contract: dict, contract: dict, canon: dict) -> set[str]:
    """Return only refs removed by deterministic contract normalization."""
    return set(effect_catalog(raw_contract, canon)) - set(
        effect_catalog(contract, canon)
    )


def _complete_equivalent_refs(rows: list, effects: dict) -> list:
    """Bind duplicate state/milestone aliases without assigning a new event."""
    return effect_binding.complete_equivalent_refs(rows, effects)
