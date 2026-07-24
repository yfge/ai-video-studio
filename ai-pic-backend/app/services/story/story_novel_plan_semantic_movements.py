"""Deterministic movement checks for semantic-audit suggestions."""

from copy import deepcopy

from .story_novel_plan_validator import _validate_chapter, _validation_context


def filter_redundant_audit_movements(audit, canon, prior_chapters, chapters):
    context = _validation_context(canon)
    for chapter in prior_chapters:
        _validate_chapter(chapter, context)
    state_after, by_position = {}, {}
    for chapter in chapters:
        position = int(chapter["position"])
        by_position[position] = chapter
        _validate_chapter(chapter, context)
        state_after[position] = deepcopy(context["state"])
    for event in audit:
        position = event["position"]
        existing = {
            (item["subject_id"], item.get("from_location_id"), item["to_location_id"])
            for item in by_position[position].get("location_transitions") or []
        }
        kept = []
        for movement in event["missing_effects"]["location_transitions"]:
            key = (
                movement["subject_id"],
                movement.get("from_location_id"),
                movement["to_location_id"],
            )
            subject = state_after[position].setdefault(movement["subject_id"], {})
            if key in existing or subject.get("location") == movement["to_location_id"]:
                continue
            kept.append(movement)
            subject["location"] = movement["to_location_id"]
        event["missing_effects"]["location_transitions"] = kept
    return audit
