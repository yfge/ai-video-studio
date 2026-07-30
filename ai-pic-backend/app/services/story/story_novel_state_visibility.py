"""Current-chapter state visibility without future Canon leakage."""


def milestone_effect_refs(
    canon: dict, refs: set[str], state_before: dict | None = None
) -> set[str]:
    """Include entities needed to execute already-visible milestone outcomes."""
    result = set(refs)
    outcome_subjects = set()
    entity_ids = {str(item["id"]) for item in canon.get("entities") or []}
    for milestone in canon.get("milestones") or []:
        if milestone.get("id") not in refs:
            continue
        for outcome in milestone.get("outcomes") or []:
            subject_id, value = outcome.get("subject_id"), outcome.get("value")
            if subject_id in entity_ids:
                result.add(str(subject_id))
                outcome_subjects.add(str(subject_id))
            if isinstance(value, str) and value in entity_ids:
                result.add(value)
    subjects = (state_before or {}).get("subjects") or {}
    result.update(
        owner_id
        for subject_id in outcome_subjects
        for owner_id in [(subjects.get(subject_id) or {}).get("owner_id")]
        if owner_id in entity_ids
    )
    return result


def state_entity_refs(
    canon: dict,
    refs: set[str],
    state_before: dict | None = None,
    *,
    revealed_refs: set[str] | None = None,
) -> set[str]:
    """Close current subject references without retaining the whole past world."""
    entities = {
        str(item["id"]): item for item in canon.get("entities") or [] if item.get("id")
    }
    subjects = (state_before or {}).get("subjects") or {}
    revealed = set(revealed_refs or refs)
    result = set(refs)
    pending = list(refs)
    while pending:
        subject = subjects.get(pending.pop()) or {}
        linked = set()
        location = subject.get("location")
        if location in entities and entities[location].get("kind") == "location":
            linked.add(location)
        owner = subject.get("owner_id")
        if owner in revealed:
            linked.add(owner)
        linked.update(
            value for value in (subject.get("relationships") or {}) if value in revealed
        )
        linked.update(
            value for value in subject.get("possessions") or [] if value in revealed
        )
        for entity_id in linked - result:
            result.add(entity_id)
            pending.append(entity_id)
    return result


def visible_state_fields(
    canon: dict, chapters: list[dict], visible_refs: set[str]
) -> dict[str, set[str]]:
    fields = {subject_id: {"location"} for subject_id in visible_refs}
    for chapter in chapters:
        for item in chapter.get("preconditions") or []:
            fields.setdefault(item["subject_id"], set()).add(_root(item["field"]))
        for item in chapter.get("state_transitions") or []:
            fields.setdefault(item["subject_id"], set()).add(_root(item["field"]))
        for item in chapter.get("location_transitions") or []:
            fields.setdefault(item["subject_id"], set()).add("location")
        for item in chapter.get("knowledge_grants") or []:
            fields.setdefault(item["character_id"], set()).add("knowledge")
    consumed = {
        value
        for chapter in chapters
        for value in chapter.get("milestones_consumed") or []
    }
    for milestone in canon.get("milestones") or []:
        if milestone.get("id") not in consumed:
            continue
        for outcome in milestone.get("outcomes") or []:
            fields.setdefault(outcome["subject_id"], set()).add(_root(outcome["field"]))
    _allow_entity_state(fields, canon)
    return fields


def visible_subject(value: dict, fields: set[str], refs: set[str]) -> dict:
    result = {key: item for key, item in value.items() if key in fields}
    if result.get("owner_id") not in refs:
        result.pop("owner_id", None)
    if isinstance(result.get("relationships"), dict):
        result["relationships"] = {
            key: item for key, item in result["relationships"].items() if key in refs
        }
    return result


def _allow_entity_state(fields: dict[str, set[str]], canon: dict) -> None:
    for item in canon.get("entities") or []:
        subject_id = item.get("id")
        if subject_id not in fields:
            continue
        if item.get("kind") == "character":
            fields[subject_id].add("relationships")
        elif item.get("kind") == "object":
            fields[subject_id].update({"owner_id", "status"})


def _root(field: str) -> str:
    return str(field).split(".", 1)[0]
