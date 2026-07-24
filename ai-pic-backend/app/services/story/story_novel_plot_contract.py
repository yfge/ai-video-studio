"""Derive the authoritative long-form plot ledger from typed state."""

from __future__ import annotations


def validated_plot_delta(chapter_plan: dict, state_delta: dict) -> dict:
    """Derive the prompt-facing plot ledger only from a passed typed delta."""
    character_states: dict[str, dict] = {}
    for item in state_delta.get("state_transitions") or []:
        character_states.setdefault(item["subject_id"], {})[item["field"]] = item.get(
            "to_value"
        )
    for item in state_delta.get("location_transitions") or []:
        character_states.setdefault(item["subject_id"], {})["location"] = item[
            "to_location_id"
        ]
    for item in state_delta.get("knowledge_grants") or []:
        knowledge = character_states.setdefault(item["character_id"], {}).setdefault(
            "knowledge_granted", []
        )
        knowledge.append(item["fact_id"])
    return {
        "key_events": list(chapter_plan.get("key_events") or []),
        "unresolved_threads": list(state_delta.get("opened_thread_ids") or []),
        "resolved_threads": list(state_delta.get("resolved_thread_ids") or []),
        "character_states": character_states,
    }
