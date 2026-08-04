"""Current-chapter knowledge sentence requirements for prose prompts."""

from __future__ import annotations

from typing import Any

from app.services.narrative_memory.knowledge_evidence import knowledge_evidence_key


def knowledge_sentence_prefixes(context_pack: dict[str, Any]) -> list[dict[str, str]]:
    hard = context_pack.get("hard_constraints") or context_pack
    chapter = hard.get("chapter_contract") or context_pack.get("chapter_contract") or {}
    canon = hard.get("compiled_canon") or {}
    event_text = dict(
        zip(
            chapter.get("required_event_ids") or [],
            chapter.get("key_events") or [],
            strict=False,
        )
    )
    names = {
        str(item.get("id") or ""): str(item.get("name") or "")
        for item in canon.get("entities") or []
        if item.get("kind") == "character" and item.get("name")
    }
    return [
        {
            "grant_key": knowledge_evidence_key(item),
            "source_event_id": str(item.get("source_event_id") or ""),
            "source_event_text": str(event_text.get(item.get("source_event_id")) or ""),
            "required_prefix": f"{names[item['character_id']]}确认",
        }
        for item in chapter.get("knowledge_grants") or []
        if item.get("character_id") in names
    ]
