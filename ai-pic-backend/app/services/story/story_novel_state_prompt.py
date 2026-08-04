"""Current-chapter state locks for prose prompts."""

from __future__ import annotations

from typing import Any

_LOCKED_FIELDS = ("location", "owner_id", "status")


def locked_state_subjects(context_pack: dict[str, Any]) -> list[dict[str, Any]]:
    hard = context_pack.get("hard_constraints") or context_pack
    chapter = hard.get("chapter_contract") or {}
    canon = hard.get("compiled_canon") or {}
    allowed = {
        str(item.get("subject_id"))
        for field in ("state_transitions", "location_transitions")
        for item in chapter.get(field) or []
        if item.get("subject_id")
    }
    moving = {
        str(item.get("subject_id"))
        for item in chapter.get("location_transitions") or []
        if item.get("subject_id")
    }
    consumed = set(chapter.get("milestones_consumed") or [])
    allowed.update(
        str(outcome.get("subject_id"))
        for milestone in canon.get("milestones") or []
        if milestone.get("id") in consumed
        for outcome in milestone.get("outcomes") or []
        if outcome.get("subject_id")
    )
    entities = {str(item.get("id")): item for item in canon.get("entities") or []}
    subjects = (hard.get("current_state") or {}).get("subjects") or {}
    result = []
    for subject_id in chapter.get("canon_refs") or []:
        subject_id = str(subject_id)
        state = subjects.get(subject_id) or {}
        locked = {key: state[key] for key in _LOCKED_FIELDS if key in state}
        if subject_id not in allowed and locked:
            entity = entities.get(subject_id) or {}
            follows_owner = (
                entity.get("kind") == "object" and str(state.get("owner_id")) in moving
            )
            if follows_owner:
                locked.pop("location", None)
            item = {
                "subject_id": subject_id,
                "name": entity.get("name") or subject_id,
                "kind": entity.get("kind"),
                "must_remain": locked,
            }
            if follows_owner:
                item["location_rule"] = "随 owner 的已授权移动同行，不得部署或留下"
            result.append(item)
    return result
