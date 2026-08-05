"""Deterministic event binding for typed chapter effects."""

import copy

_REF_PREFIXES = {"S": "state", "L": "location", "K": "knowledge"}


def normalize_effect_ref_aliases(rows: list) -> list:
    """Expand unambiguous S1/L1/K1 model shorthands without changing ownership."""
    result = copy.deepcopy(rows)
    for row in result:
        for review in row.get("field_reviews") or []:
            review["effect_refs"] = [
                _canonical_ref(ref) for ref in review.get("effect_refs") or []
            ]
    return result


def _canonical_ref(value) -> str:
    ref = str(value)
    prefix, index = ref[:1], ref[1:]
    return (
        f"{_REF_PREFIXES[prefix]}:{index}"
        if prefix in _REF_PREFIXES and index.isdigit()
        else ref
    )


def bind_sourced_effects(rows: list, effects: dict) -> None:
    """Bind effects whose authoritative contract already names their event."""
    for row in rows:
        reviews = row.get("field_reviews") if isinstance(row, dict) else None
        if not isinstance(reviews, list):
            continue
        by_pair = {
            (item.get("subject_id"), item.get("field")): item
            for item in reviews
            if isinstance(item, dict)
        }
        for ref, (pair, source_event_id, _) in effects.items():
            if source_event_id != row.get("event_id"):
                continue
            review = by_pair.get(pair)
            if review is None:
                review = {
                    "subject_id": pair[0],
                    "field": pair[1],
                    "reason": "由章节合同的 source_event_id 确定性绑定",
                }
                reviews.append(review)
                by_pair[pair] = review
            refs = list(review.get("effect_refs") or [])
            if ref not in refs:
                review.update(disposition="changed", effect_refs=[*refs, ref])


def complete_equivalent_refs(rows: list, effects: dict) -> list:
    """Complete sourced, equivalent and uniquely owned atomic milestone refs."""
    result = copy.deepcopy(rows)
    _relocate_sourced_effects(result, effects)
    bind_sourced_effects(result, effects)
    _bind_equivalent_aliases(result, effects)
    _bind_atomic_milestone_outcomes(result, effects)
    _bind_equivalent_aliases(result, effects)
    return result


def _relocate_sourced_effects(rows: list, effects: dict) -> None:
    """Let an authoritative source event own its effect's subject and field."""
    for row in rows:
        if not isinstance(row, dict):
            continue
        event_id = row.get("event_id")
        for review in row.get("field_reviews") or []:
            pair = (review.get("subject_id"), review.get("field"))
            review["effect_refs"] = [
                ref
                for ref in review.get("effect_refs") or []
                if not (
                    effects.get(ref)
                    and effects[ref][1] == event_id
                    and effects[ref][0] != pair
                )
            ]


def _bind_equivalent_aliases(rows: list, effects: dict) -> None:
    for row in rows:
        if not isinstance(row, dict):
            continue
        event_id = row.get("event_id")
        for review in row.get("field_reviews") or []:
            refs = list(
                dict.fromkeys(str(value) for value in review.get("effect_refs") or [])
            )
            for ref in list(refs):
                source = effects.get(ref)
                if not source or source[1] not in {None, event_id}:
                    continue
                for candidate, target in effects.items():
                    if candidate in refs or not _alias_pair(ref, candidate):
                        continue
                    if target[1] not in {None, event_id}:
                        continue
                    if source[0] == target[0] and _same_outcome(source[2], target[2]):
                        refs.append(candidate)
            review["effect_refs"] = refs


def _bind_atomic_milestone_outcomes(rows: list, effects: dict) -> None:
    owners: dict[str, dict[str, dict]] = {}
    for row in rows:
        for review in row.get("field_reviews") or []:
            for ref in review.get("effect_refs") or []:
                milestone_id = _milestone_id(ref)
                if milestone_id and row.get("event_id"):
                    owners.setdefault(milestone_id, {})[row["event_id"]] = row
    for milestone_id, event_rows in owners.items():
        if len(event_rows) != 1:
            continue
        row = next(iter(event_rows.values()))
        reviews = row.get("field_reviews") or []
        by_pair = {
            (item.get("subject_id"), item.get("field")): item
            for item in reviews
            if isinstance(item, dict)
        }
        for ref, (pair, _source_event_id, _outcome) in effects.items():
            if _milestone_id(ref) != milestone_id:
                continue
            review = by_pair.get(pair)
            if review is None:
                review = {
                    "subject_id": pair[0],
                    "field": pair[1],
                    "reason": "由同一原子里程碑的唯一事件归属确定性绑定",
                }
                reviews.append(review)
                by_pair[pair] = review
            refs = list(review.get("effect_refs") or [])
            if ref not in refs:
                review.update(disposition="changed", effect_refs=[*refs, ref])


def _milestone_id(ref: str) -> str | None:
    parts = str(ref).split(":", 2)
    return parts[1] if len(parts) == 3 and parts[0] == "milestone" else None


def _alias_pair(left: str, right: str) -> bool:
    return left.startswith("milestone:") != right.startswith("milestone:")


def _same_outcome(left: dict, right: dict) -> bool:
    if left == right:
        return True
    if left["operator"] == "eq" and right["operator"] == "contains":
        return isinstance(left["value"], list) and right["value"] in left["value"]
    if right["operator"] == "eq" and left["operator"] == "contains":
        return isinstance(right["value"], list) and left["value"] in right["value"]
    return False


def normalize_top_level_effect_refs(rows: list, effects: dict) -> list:
    """Move an unambiguous model shorthand into typed field reviews."""
    result = normalize_effect_ref_aliases(rows)
    for row in result:
        if not isinstance(row, dict) or "effect_refs" not in row:
            continue
        refs = list(dict.fromkeys(str(value) for value in row.pop("effect_refs") or []))
        if row.get("field_reviews") or not refs:
            row["effect_refs"] = refs
            continue
        grouped = {}
        for ref in refs:
            effect = effects.get(ref)
            if not effect:
                row["effect_refs"] = refs
                break
            grouped.setdefault(effect[0], []).append(ref)
        else:
            reason = str(row.get("rationale") or "typed effect 归属当前事件")
            row["field_reviews"] = [
                {
                    "subject_id": pair[0],
                    "field": pair[1],
                    "disposition": "changed",
                    "effect_refs": pair_refs,
                    "reason": reason,
                }
                for pair, pair_refs in grouped.items()
            ]
    return result
