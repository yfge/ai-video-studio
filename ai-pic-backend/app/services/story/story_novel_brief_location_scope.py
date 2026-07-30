"""Deterministic location scope for newly generated v3 chapter briefs."""

import copy


def normalize_model_brief(brief: dict, allowed: set[str]) -> dict:
    """Normalize harmless provider aliases before strict brief validation."""
    result = copy.deepcopy(brief)
    for beat in result.get("beats") or []:
        beat["allowed_entity_ids"] = [
            value for value in beat.get("allowed_entity_ids") or [] if value in allowed
        ]
        beat["effect_contract_ids"] = [
            value.removeprefix("contract_id:") if isinstance(value, str) else value
            for value in beat.get("effect_contract_ids") or []
        ]
    return result


def brief_allowed_entity_ids(brief_input: dict) -> list[str]:
    """Keep all visible non-locations but only current-path locations."""
    entities, locations, allowed = _scope(brief_input)
    return [
        entity_id
        for entity_id in brief_input.get("allowed_entity_ids") or []
        if entity_id not in locations or entity_id in allowed
    ]


def validate_brief_location_scope(beats: list[dict], brief_input: dict) -> None:
    _entities, locations, allowed = _scope(brief_input)
    if not locations:
        return
    invalid = {
        beat.get("beat_id"): sorted(
            set(beat.get("allowed_entity_ids") or []).intersection(locations) - allowed
        )
        for beat in beats
    }
    invalid = {key: value for key, value in invalid.items() if value}
    if invalid:
        raise ValueError(
            f"chapter brief 地点实体超出本章允许路径: {invalid}; "
            f"允许地点: {sorted(allowed)}"
        )


def _scope(brief_input: dict) -> tuple[dict, set[str], set[str]]:
    canon = (brief_input.get("hard_constraints") or {}).get("compiled_canon") or {}
    entities = {
        item.get("id"): item for item in canon.get("entities") or [] if item.get("id")
    }
    locations = {
        entity_id
        for entity_id, item in entities.items()
        if item.get("kind") == "location"
    }
    contract = brief_input.get("chapter_contract") or {}
    subjects = (brief_input.get("state_before") or {}).get("subjects") or {}
    active = _active_subject_ids(contract, entities)
    allowed = {
        value
        for item in contract.get("location_transitions") or []
        for value in (item.get("from_location_id"), item.get("to_location_id"))
        if value in locations
    }
    allowed.update(
        state.get("location")
        for subject_id, state in subjects.items()
        if subject_id in active and state.get("location") in locations
    )
    allowed.update(set(contract.get("canon_refs") or []).intersection(locations))
    _include_parent_locations(allowed, entities, locations)
    return entities, locations, allowed


def _active_subject_ids(contract: dict, entities: dict) -> set[str]:
    result = {
        value
        for key in ("state_transitions", "location_transitions")
        for item in contract.get(key) or []
        for value in (item.get("subject_id"),)
        if value
    }
    result.update(
        item.get("character_id") for item in contract.get("knowledge_grants") or []
    )
    result.update(
        actor
        for item in contract.get("execution_contracts") or []
        for actor in item.get("actor_ids") or []
    )
    focus = set(contract.get("character_focus") or [])
    result.update(
        entity_id
        for entity_id, item in entities.items()
        if item.get("kind") == "character"
        and focus.intersection({item.get("name"), *(item.get("aliases") or [])})
    )
    return {value for value in result if value}


def _include_parent_locations(allowed: set, entities: dict, locations: set) -> None:
    pending = list(allowed)
    while pending:
        entity_id = pending.pop()
        parent = (
            (entities.get(entity_id) or {})
            .get("attributes", {})
            .get("parent_location_id")
        )
        if parent in locations and parent not in allowed:
            allowed.add(parent)
            pending.append(parent)
