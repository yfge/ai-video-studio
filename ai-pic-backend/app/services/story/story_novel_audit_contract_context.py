"""Build the compact current-chapter semantic context for proof audit."""

from __future__ import annotations

from .story_novel_v3_audit_semantics import current_timeline_context


def audit_contract_context(
    chapter_plan: dict,
    brief: dict | None,
    expected_delta: dict,
    canon: dict,
    established_background=None,
) -> dict:
    event_ids = list(chapter_plan.get("required_event_ids") or [])
    event_texts = list(chapter_plan.get("key_events") or [])
    if len(event_ids) != len(event_texts):
        raise ValueError("当前章 event ID 与 key_event 未一一对应")
    characters = {
        item.get("id"): item
        for item in canon.get("entities") or []
        if item.get("kind") == "character"
    }
    event_text = dict(zip(event_ids, event_texts, strict=True))
    semantics = chapter_plan.get("effect_semantics") or {}
    bindings = chapter_plan.get("effect_event_bindings") or {}
    return {
        "established_background": list(established_background or []),
        "current_timeline": current_timeline_context(canon, chapter_plan),
        "execution_contracts": list(chapter_plan.get("execution_contracts") or []),
        "current_events": [
            {"event_id": event_id, "key_event": event_text[event_id]}
            for event_id in event_ids
        ],
        "knowledge_semantics": [
            {
                "contract_id": f"knowledge:{index}",
                **grant,
                "meaning": semantics.get(f"knowledge:{index}"),
                "character_names": _character_names(
                    characters.get(grant.get("character_id")) or {}
                ),
                "source_key_event": event_text.get(grant.get("source_event_id")),
            }
            for index, grant in enumerate(
                expected_delta.get("knowledge_grants") or [], start=1
            )
        ],
        "entity_introduction_semantics": [
            {
                "contract_id": f"entity:{item['id']}",
                "kind": item.get("kind"),
                "name": item.get("name"),
                "aliases": list(item.get("aliases") or []),
                "narrative_function": (item.get("attributes") or {}).get(
                    "narrative_function"
                ),
                "profile": (item.get("attributes") or {}).get("profile"),
                "initial_relationships": (item.get("initial_state") or {}).get(
                    "relationships"
                )
                or {},
                "source_event_id": item.get("source_event_id"),
            }
            for item in expected_delta.get("entity_introductions") or []
        ],
        "effect_semantics": [
            {
                "contract_id": contract_id,
                "meaning": meaning,
                "source_event_id": bindings.get(contract_id),
            }
            for contract_id, meaning in semantics.items()
        ],
        "current_beats": [
            {
                key: beat.get(key)
                for key in (
                    "beat_id",
                    "purpose",
                    "bound_event_ids",
                    "effect_contract_ids",
                )
            }
            for beat in (brief or {}).get("beats") or []
        ],
        "continuity_watchpoints": list(
            (brief or {}).get("continuity_watchpoints") or []
        ),
    }


def _character_names(entity: dict) -> list[str]:
    return [
        str(value)
        for value in [entity.get("name"), *(entity.get("aliases") or [])]
        if str(value or "").strip()
    ]
