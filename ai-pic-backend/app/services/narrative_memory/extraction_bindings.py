"""Map typed Canon characters to persisted StoryCharacter identities."""

import re

from app.core.exceptions import ServiceError
from app.services.narrative_memory.knowledge_evidence import (
    knowledge_evidence_key,
    knowledge_grant_key,
)


def knowledge_character_bindings(
    canon: dict,
    delta: dict,
    characters: list[dict],
) -> dict[str, dict]:
    entities = {
        item["id"]: item
        for item in canon.get("entities") or []
        if item.get("kind") == "character"
    }
    bindings = {}
    required_keys = set()
    for grant in delta.get("knowledge_grants") or []:
        canonical_id = grant.get("character_id")
        entity = entities.get(canonical_id) or {}
        names = [
            _semantic(value)
            for value in [entity.get("name"), *(entity.get("aliases") or [])]
            if _semantic(str(value or ""))
        ]
        matches = [
            item["character_business_id"]
            for item in characters
            if item["character_business_id"] == canonical_id
            or any(
                name in _semantic(item["name"]) or _semantic(item["name"]) in name
                for name in names
            )
        ]
        if not matches:
            continue
        required_keys.add(knowledge_grant_key(grant))
        if len(matches) != 1:
            continue
        existing = bindings.get(matches[0])
        if existing and existing["typed_character_id"] != canonical_id:
            continue
        binding = bindings.setdefault(
            matches[0],
            {
                "typed_character_id": canonical_id,
                "names": names,
                "grants": [],
            },
        )
        binding["grants"].append(
            {
                "character_id": canonical_id,
                "fact_id": grant.get("fact_id"),
                "source_event_id": grant.get("source_event_id"),
                "evidence": str(
                    (delta.get("knowledge_evidence") or {}).get(
                        knowledge_evidence_key(grant)
                    )
                    or ""
                ),
            }
        )
        if not binding["grants"][-1]["evidence"]:
            binding["grants"].pop()
    if required_keys != bound_knowledge_grant_keys(bindings):
        raise ServiceError(
            "记忆候选提取失败：typed knowledge grant 无法唯一映射 StoryCharacter"
        )
    return bindings


def knowledge_grant_keys(delta: dict) -> set[tuple[str, str, str]]:
    return {
        knowledge_grant_key(item)
        for item in delta.get("knowledge_grants") or []
        if all(
            item.get(field) for field in ("character_id", "fact_id", "source_event_id")
        )
    }


def bound_knowledge_grant_keys(
    bindings: dict[str, dict],
) -> set[tuple[str, str, str]]:
    return {
        knowledge_grant_key(grant)
        for binding in bindings.values()
        for grant in binding.get("grants") or []
    }


def _semantic(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", value)
