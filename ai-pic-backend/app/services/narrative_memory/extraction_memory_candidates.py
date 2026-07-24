"""Build typed-state-bound Character Memory candidates."""

from __future__ import annotations

import re

from app.core.exceptions import ServiceError
from app.schemas.narrative_memory import CharacterMemoryCandidateCreate
from app.services.narrative_memory.knowledge_evidence import (
    explicit_knowledge_acquisition,
)


def build_memory_candidates(
    raw_memories: list[dict],
    anchors: dict,
    characters: dict,
    *,
    strict: bool,
    character_bindings: dict[str, dict],
    verification_version: int,
) -> list[CharacterMemoryCandidateCreate]:
    memories = [
        _memory_candidate(
            raw,
            anchors,
            characters,
            strict=strict,
            character_bindings=character_bindings,
            verification_version=verification_version,
        )
        for raw in raw_memories
    ]
    if strict:
        _require_typed_memory_coverage(memories, character_bindings)
    return memories


def _memory_candidate(
    raw: dict,
    anchors: dict,
    characters: dict,
    *,
    strict: bool,
    character_bindings: dict[str, dict],
    verification_version: int,
) -> CharacterMemoryCandidateCreate:
    item = dict(raw)
    source_quote = item.pop("evidence")
    growth_delta = item.pop("growth_delta", None)
    typed_grant = {
        "character_id": item.pop("typed_character_id", None),
        "fact_id": item.pop("typed_fact_id", None),
        "source_event_id": item.pop("typed_source_event_id", None),
    }
    character = characters.get(item["character_business_id"])
    if strict and (
        character is None
        or character["virtual_ip_business_id"] != item["virtual_ip_business_id"]
    ):
        raise ServiceError("记忆候选提取失败：角色或 Virtual IP 不属于当前 Story")
    learned = _anchor(anchors, item["learned_at_anchor_business_id"], strict)
    for field in (
        "occurred_at_anchor_business_id",
        "effective_from_anchor_business_id",
        "invalidated_at_anchor_business_id",
    ):
        if item.get(field):
            item[field] = _anchor(anchors, item[field], strict).business_id
    item["learned_at_anchor_business_id"] = learned.business_id
    item["effective_from_anchor_business_id"] = (
        item.get("effective_from_anchor_business_id") or learned.business_id
    )
    binding = character_bindings.get(item["character_business_id"])
    if strict:
        allowed_grants = {
            _grant_key(grant): grant for grant in (binding or {}).get("grants") or []
        }
        expected_quote = (allowed_grants.get(_grant_key(typed_grant)) or {}).get(
            "evidence"
        )
        if (
            not binding
            or _grant_key(typed_grant) not in allowed_grants
            or not expected_quote
            or _semantic(source_quote) != _semantic(expected_quote)
            or not explicit_knowledge_acquisition(source_quote, binding["names"])
        ):
            raise ServiceError("记忆候选提取失败：角色知识未绑定对应 typed grant")
        item.update(
            content=source_quote,
            belief=None,
            belief_confidence=None,
            perception=None,
            emotional_impact=[],
        )
    evidence = {
        "source_quote": source_quote,
        "source_quote_verified": True,
    }
    if strict:
        evidence.update(
            claim_verified=True,
            claim_mode="typed_state_bound",
            verification_version=verification_version,
            typed_state_binding_verified=True,
            typed_character_id=typed_grant["character_id"],
            typed_fact_id=typed_grant["fact_id"],
            typed_source_event_id=typed_grant["source_event_id"],
        )
    elif growth_delta:
        evidence["growth_delta"] = growth_delta
    return CharacterMemoryCandidateCreate(
        **item,
        source_artifact_type=learned.source_artifact_type,
        source_artifact_business_id=learned.source_artifact_business_id,
        source_version=learned.source_version,
        source_hash=learned.source_hash,
        candidate_evidence=evidence,
    )


def _require_typed_memory_coverage(
    memories: list[CharacterMemoryCandidateCreate],
    bindings: dict[str, dict],
) -> None:
    expected = {
        _grant_key(grant)
        for binding in bindings.values()
        for grant in binding.get("grants") or []
    }
    supplied = {
        (
            evidence.get("typed_character_id"),
            evidence.get("typed_fact_id"),
            evidence.get("typed_source_event_id"),
        )
        for item in memories
        for evidence in [item.candidate_evidence or {}]
    }
    if expected != supplied or len(memories) != len(supplied):
        raise ServiceError("记忆候选提取失败：角色知识未逐项覆盖 typed grant")


def _anchor(anchors: dict, business_id: str, strict: bool):
    anchor = anchors.get(business_id)
    if anchor is None and strict:
        raise ServiceError(f"记忆候选提取失败：未知来源锚点 {business_id}")
    return anchor or next(iter(anchors.values()))


def _grant_key(item: dict) -> tuple[str | None, str | None, str | None]:
    return (
        item.get("character_id"),
        item.get("fact_id"),
        item.get("source_event_id"),
    )


def _semantic(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", value)
