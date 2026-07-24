"""Bind model knowledge grants to exact Canon milestone facts."""

from __future__ import annotations


def normalize_milestone_knowledge(
    chapter: dict, canon: dict | None, thread_payoffs: list[dict] | None
) -> list:
    grants = [dict(item) for item in chapter.get("knowledge_grants") or []]
    milestones = {
        item["id"]: item
        for item in (canon or {}).get("milestones") or []
        if item.get("id")
    }
    required = set(chapter.get("required_event_ids") or [])
    payoff_event_id = _payoff_event_id(chapter, thread_payoffs)
    for milestone_id in chapter.get("milestones_consumed") or []:
        for outcome in (milestones.get(milestone_id) or {}).get("outcomes") or []:
            if (
                outcome.get("field") != "knowledge"
                or outcome.get("operator") != "contains"
            ):
                continue
            character_id, fact_id = outcome.get("subject_id"), outcome.get("value")
            if not isinstance(fact_id, str) or any(
                item.get("character_id") == character_id
                and item.get("fact_id") == fact_id
                for item in grants
            ):
                continue
            candidates = [
                item
                for item in grants
                if item.get("character_id") == character_id
                and item.get("source_event_id") in required
                and isinstance(item.get("fact_id"), str)
                and fact_id in item["fact_id"]
            ]
            if not candidates and payoff_event_id:
                candidates = [
                    item
                    for item in grants
                    if item.get("character_id") == character_id
                    and item.get("source_event_id") == payoff_event_id
                ]
            if len(candidates) == 1:
                candidates[0]["fact_id"] = fact_id
            elif not candidates and payoff_event_id:
                grants.append(
                    {
                        "character_id": character_id,
                        "fact_id": fact_id,
                        "source_event_id": payoff_event_id,
                    }
                )
    return grants


def _payoff_event_id(chapter: dict, thread_payoffs: list[dict] | None) -> str | None:
    key_events = list(chapter.get("key_events") or [])
    event_ids = list(chapter.get("required_event_ids") or [])
    position = int(chapter.get("position") or 0)
    evidence = {
        item.get("evidence_key_event")
        for item in thread_payoffs or []
        if int(item.get("payoff_position") or 0) == position
    }
    matches = {
        event_ids[index]
        for index, key_event in enumerate(key_events)
        if key_event in evidence and index < len(event_ids)
    }
    return next(iter(matches)) if len(matches) == 1 else None
