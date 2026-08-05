"""Compile local semantic effects into exact state edges from one snapshot."""

from __future__ import annotations

import copy

from .story_novel_context_utils import value_hash
from .story_novel_effect_semantics import default_effect_meanings, intent_effect_meaning
from .story_novel_milestone_effect_compiler import compile_milestone_effects
from .story_novel_state_service import get_state_value

_LIST_FIELDS = {
    "capability_add": ("capabilities", "add"),
    "capability_remove": ("capabilities", "remove"),
    "resource_add": ("resources", "add"),
    "resource_remove": ("resources", "remove"),
    "permission_add": ("permissions", "add"),
    "permission_remove": ("permissions", "remove"),
}


def effect_model_input(snapshot: dict, intent: dict) -> dict:
    model_input = copy.deepcopy(snapshot["model_input"])
    model_input.setdefault("visible_characters_and_world", []).extend(
        {
            "entity_handle": item["proposal_handle"],
            "kind": item["kind"],
            "name": item["name"],
        }
        for item in intent.get("entity_proposals") or []
        if not item["transient"]
    )
    return model_input


def compile_intent_effects(
    skeleton: dict,
    intent: dict,
    snapshot: dict,
    canon: dict,
    effect_context: dict | None = None,
) -> tuple[dict, dict[str, str], dict[str, str]]:
    """Return typed effects and exact proof-to-event bindings."""
    effect_context = effect_context or {}
    state_before = (
        effect_context.get("state_before")
        or snapshot["execution_context"]["state_before"]
    )
    subjects = state_before.get("subjects") or {}
    events = snapshot["handle_bindings"]["events"]
    entities = effect_context.get("entities") or snapshot["handle_bindings"]["entities"]
    row = compile_milestone_effects(
        canon,
        {
            "required_event_ids": list(skeleton.get("required_event_ids") or []),
            "milestones_consumed": list(skeleton.get("milestones_consumed") or []),
            "state_transitions": copy.deepcopy(skeleton.get("state_transitions") or []),
            "knowledge_grants": copy.deepcopy(skeleton.get("knowledge_grants") or []),
            "location_transitions": copy.deepcopy(
                skeleton.get("location_transitions") or []
            ),
        },
        subjects,
    )
    default_event = next(reversed(events.values()), None)
    bindings = _default_bindings(row, default_event)
    meanings = default_effect_meanings(row, snapshot)
    ignored = []
    for effect in intent.get("effect_intents") or []:
        source_event = events[effect["source_event_handle"]]
        subject_id = entities[effect["subject_handle"]]
        kind = effect["kind"]
        if kind == "knowledge_gain":
            ref = _knowledge(row, subjects, subject_id, source_event, effect)
        elif kind == "location_change":
            ref = _movement(row, subjects, subject_id, entities, effect)
        else:
            ref = _transition(row, subjects, subject_id, entities, effect)
        if ref is None:
            ignored.append(
                {
                    "effect_handle": effect["effect_handle"],
                    "kind": effect["kind"],
                    "reason": "no_persistent_state_change",
                }
            )
            continue
        bindings[ref] = source_event
        if kind in {"state_change", "status_change"}:
            for index, grant in enumerate(row["knowledge_grants"], 1):
                if grant.get("fact_id") == subject_id:
                    grant["source_event_id"] = source_event
                    bindings[f"knowledge:{index}"] = source_event
        meanings[ref] = intent_effect_meaning(
            effect, effect_context.get("model_input") or snapshot["model_input"]
        )
    return (
        {
            "state_transitions": row["state_transitions"],
            "knowledge_grants": row["knowledge_grants"],
            "location_transitions": row["location_transitions"],
            "ignored_effect_intents": ignored,
        },
        bindings,
        meanings,
    )


def _transition(row, subjects, subject_id, entities, effect) -> str | None:
    kind = effect["kind"]
    field, target = _transition_target(kind, effect, subjects, subject_id, entities)
    current = get_state_value(subjects.get(subject_id) or {}, field)
    matches = [
        (index, item)
        for index, item in enumerate(row["state_transitions"], 1)
        if item.get("subject_id") == subject_id and item.get("field") == field
    ]
    if matches:
        index, existing = matches[0]
        if len(matches) > 1 or existing.get("to_value") != target:
            raise ValueError(f"effect_intent 与既有状态合同冲突: {subject_id}.{field}")
        return f"state:{index}"
    if current == target:
        return None
    row["state_transitions"].append(
        {
            "subject_id": subject_id,
            "field": field,
            "from_value": copy.deepcopy(current),
            "to_value": copy.deepcopy(target),
            "reason": f"chapter intent {effect['effect_handle']}",
        }
    )
    return f"state:{len(row['state_transitions'])}"


def _transition_target(kind, effect, subjects, subject_id, entities):
    if kind in _LIST_FIELDS:
        field, operation = _LIST_FIELDS[kind]
        current = get_state_value(subjects.get(subject_id) or {}, field)
        current = [] if current is None else copy.deepcopy(current)
        if not isinstance(current, list):
            raise ValueError(f"{subject_id}.{field} 不是数组状态")
        value = effect["value"]
        if operation == "add":
            if value in current:
                return field, current
            return field, [*current, value]
        if value not in current:
            return field, current
        return field, [item for item in current if item != value]
    if kind == "relationship_change":
        return f"relationships.{entities[effect['target_handle']]}", effect["value"]
    if kind == "ownership_change":
        return "owner_id", entities[effect["target_handle"]]
    if kind == "status_change":
        return "status", effect["value"]
    if kind == "state_change":
        return effect["field"], copy.deepcopy(effect["value"])
    raise ValueError(f"未知 effect kind: {kind}")


def _knowledge(row, subjects, character_id, event_id, effect) -> str:
    fact_id = "fact-v4-{}-{}".format(
        effect["effect_handle"].lower(),
        value_hash({"event": event_id, "value": effect["value"]})[:12],
    )
    if fact_id in ((subjects.get(character_id) or {}).get("knowledge") or []):
        raise ValueError(f"effect_intent 重复授予既有知识: {character_id}->{fact_id}")
    matches = [
        (index, item)
        for index, item in enumerate(row["knowledge_grants"], 1)
        if item.get("character_id") == character_id and item.get("fact_id") == fact_id
    ]
    if matches:
        index, existing = matches[0]
        if existing.get("source_event_id") != event_id:
            raise ValueError("effect_intent 知识来源事件冲突")
        return f"knowledge:{index}"
    row["knowledge_grants"].append(
        {
            "character_id": character_id,
            "fact_id": fact_id,
            "source_event_id": event_id,
        }
    )
    return f"knowledge:{len(row['knowledge_grants'])}"


def _movement(row, subjects, subject_id, entities, effect) -> str | None:
    target = entities[effect["target_handle"]]
    current = (subjects.get(subject_id) or {}).get("location")
    matches = [
        (index, item)
        for index, item in enumerate(row["location_transitions"], 1)
        if item.get("subject_id") == subject_id
    ]
    if matches:
        index, existing = matches[0]
        if len(matches) > 1 or existing.get("to_location_id") != target:
            raise ValueError(f"effect_intent 与既有地点合同冲突: {subject_id}")
        return f"location:{index}"
    if current == target:
        return None
    row["location_transitions"].append(
        {
            "subject_id": subject_id,
            "from_location_id": current,
            "to_location_id": target,
            "means": effect["means"],
        }
    )
    return f"location:{len(row['location_transitions'])}"


def _default_bindings(row: dict, event_id: str | None) -> dict[str, str]:
    if not event_id:
        return {}
    return {
        **{
            f"state:{index}": event_id
            for index, _ in enumerate(row["state_transitions"], 1)
        },
        **{
            f"location:{index}": event_id
            for index, _ in enumerate(row["location_transitions"], 1)
        },
        **{
            f"knowledge:{index}": item.get("source_event_id") or event_id
            for index, item in enumerate(row["knowledge_grants"], 1)
        },
    }
