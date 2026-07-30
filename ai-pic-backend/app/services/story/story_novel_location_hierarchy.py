"""Typed hierarchy for durable versus scene-only Canon locations."""

from __future__ import annotations

LOCATION_SCOPES = {"persistent", "scene"}


def location_hierarchy_issues(canon: dict) -> list[str]:
    entities = {
        item["id"]: item for item in canon.get("entities") or [] if item.get("id")
    }
    locations = {
        entity_id: item
        for entity_id, item in entities.items()
        if item.get("kind") == "location"
    }
    errors: list[str] = []
    for entity_id, item in entities.items():
        attributes = item.get("attributes") or {}
        scope = attributes.get("location_scope")
        parent = attributes.get("parent_location_id")
        if item.get("kind") != "location":
            if scope is not None or parent is not None:
                errors.append(f"非地点实体不能声明地点层级: {entity_id}")
            continue
        if scope is not None and scope not in LOCATION_SCOPES:
            errors.append(f"地点 scope 无效: {entity_id}={scope!r}")
        if scope == "scene" and not parent:
            errors.append(f"scene 地点缺少 parent_location_id: {entity_id}")
        if parent is not None and parent not in locations:
            errors.append(f"地点 parent 引用无效: {entity_id}->{parent}")
        if parent == entity_id:
            errors.append(f"地点 parent 不能引用自身: {entity_id}")
    errors.extend(_cycle_issues(locations))
    scene_ids = {
        location_id
        for location_id, item in locations.items()
        if _scope(item) == "scene"
    }
    for subject_id, state in (canon.get("initial_state") or {}).items():
        if isinstance(state, dict) and state.get("location") in scene_ids:
            errors.append(f"初始持久地点不能引用 scene location: {subject_id}")
    for milestone in canon.get("milestones") or []:
        for outcome in milestone.get("outcomes") or []:
            if outcome.get("field") != "location":
                continue
            target = outcome.get("value")
            if target not in locations:
                errors.append(f"里程碑引用未知地点: {milestone['id']}->{target}")
            elif target in scene_ids:
                errors.append(
                    f"里程碑持久地点不能引用 scene location: {milestone['id']}"
                )
    return errors


def persistent_location_id(canon: dict, location_id: object) -> object:
    """Map a scene-only location to its durable Canon ancestor."""
    if not isinstance(location_id, str) or not location_id:
        return location_id
    locations = {
        item["id"]: item
        for item in canon.get("entities") or []
        if item.get("kind") == "location" and item.get("id")
    }
    current = location_id
    seen: set[str] = set()
    while current not in seen:
        seen.add(current)
        item = locations.get(current)
        if not item or _scope(item) != "scene":
            return current
        parent = (item.get("attributes") or {}).get("parent_location_id")
        if not isinstance(parent, str) or not parent:
            return current
        current = parent
    return location_id


def normalize_persistent_locations(canon: dict, chapter: dict) -> dict:
    """Compile scene movements and predicates into durable state locations."""
    row = dict(chapter)
    predicates = []
    for raw in row.get("preconditions") or []:
        item = dict(raw)
        if item.get("field") == "location":
            item["value"] = _plan_location_id(canon, item.get("value"))
        predicates.append(item)
    movements = []
    for raw in row.get("location_transitions") or []:
        item = dict(raw)
        raw_from, raw_to = item.get("from_location_id"), item.get("to_location_id")
        item["from_location_id"] = _plan_location_id(canon, raw_from)
        item["to_location_id"] = _plan_location_id(canon, raw_to)
        collapsed_scene_move = (
            raw_from != raw_to and item["from_location_id"] == item["to_location_id"]
        )
        if not collapsed_scene_move:
            movements.append(item)
    row["preconditions"] = predicates
    row["location_transitions"] = movements
    return row


def _plan_location_id(canon: dict, location_id: object) -> object:
    """Resolve only an unambiguous expanded provider ID before validation."""
    if not isinstance(location_id, str) or not location_id.startswith("loc-"):
        return persistent_location_id(canon, location_id)
    locations = {
        item["id"]
        for item in canon.get("entities") or []
        if item.get("kind") == "location" and item.get("id")
    }
    if location_id in locations:
        return persistent_location_id(canon, location_id)
    supplied = set(location_id.removeprefix("loc-").split("-"))
    candidates = [
        candidate
        for candidate in locations
        if len(candidate.removeprefix("loc-").split("-")) >= 2
        and set(candidate.removeprefix("loc-").split("-")) < supplied
    ]
    resolved = candidates[0] if len(candidates) == 1 else location_id
    return persistent_location_id(canon, resolved)


def _scope(item: dict) -> str:
    return str((item.get("attributes") or {}).get("location_scope") or "persistent")


def _cycle_issues(locations: dict[str, dict]) -> list[str]:
    errors = []
    for location_id in locations:
        current = location_id
        path: set[str] = set()
        while current in locations:
            if current in path:
                errors.append(f"地点 parent 存在环: {location_id}")
                break
            path.add(current)
            parent = (locations[current].get("attributes") or {}).get(
                "parent_location_id"
            )
            if not isinstance(parent, str) or not parent:
                break
            current = parent
    return errors
