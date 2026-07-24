"""Build prompt-safe candidates from source-verified extraction output."""

from __future__ import annotations

import re

from app.core.exceptions import ServiceError
from app.schemas.narrative_memory import (
    CandidateDeltaCreate,
    NarrativeEventCandidateCreate,
)

from .extraction_bindings import knowledge_character_bindings
from .extraction_memory_candidates import build_memory_candidates

__all__ = ["build_candidate_payload", "knowledge_character_bindings"]

CLAIM_VERIFICATION_VERSION = 3


def build_candidate_payload(
    normalized: dict,
    anchors: list,
    characters: list[dict],
    *,
    strict: bool,
    memory_character_bindings: dict[str, dict] | None = None,
    occurred_event_ids: list[str] | None = None,
    occurred_event_evidence: dict[str, str] | None = None,
) -> CandidateDeltaCreate:
    anchor_by_id = {item.business_id: item for item in anchors}
    character_by_id = {item["character_business_id"]: item for item in characters}
    expected_events = occurred_event_evidence or {
        event_id: "" for event_id in occurred_event_ids or []
    }
    raw_events = list(normalized.get("events") or [])
    if strict:
        _require_typed_event_coverage(raw_events, expected_events)
    events = [
        _event_candidate(
            raw,
            anchor_by_id,
            character_by_id,
            strict=strict,
            expected_events=expected_events,
        )
        for raw in raw_events
    ]
    events = [item for item in events if item is not None]
    if strict and (normalized.get("events") or occurred_event_ids) and not events:
        raise ServiceError("记忆候选提取失败：当前章客观事件均未通过来源绑定")
    memories = build_memory_candidates(
        list(normalized.get("memories") or []),
        anchor_by_id,
        character_by_id,
        strict=strict,
        character_bindings=memory_character_bindings or {},
        expected_events=expected_events,
        verification_version=CLAIM_VERIFICATION_VERSION,
    )
    return CandidateDeltaCreate(events=events, memories=memories)


def _event_candidate(
    raw: dict,
    anchors: dict,
    characters: dict,
    *,
    strict: bool,
    expected_events: dict[str, str],
):
    item = dict(raw)
    source_quote = item.pop("evidence")
    typed_event_ids = list(item.pop("typed_event_ids", []) or [])
    anchor = _anchor(anchors, item["occurred_at_anchor_business_id"], strict)
    participant_ids = list(item.get("participant_character_ids") or [])
    unknown = set(participant_ids) - set(characters)
    if strict and unknown:
        raise ServiceError(f"记忆候选提取失败：事件包含未知角色 {sorted(unknown)}")
    if strict:
        expected_quote = expected_events[typed_event_ids[0]]
        if expected_quote and _semantic(source_quote) != _semantic(expected_quote):
            raise ServiceError("记忆候选提取失败：客观事件证据未绑定对应 typed event")
        quote_text = _semantic(source_quote)
        participant_ids = [
            identifier
            for identifier in participant_ids
            if _semantic(characters[identifier]["name"]) in quote_text
        ]
        item.update(
            summary=source_quote,
            participant_character_ids=participant_ids,
            occurred_at_anchor_business_id=anchor.business_id,
            presentation="on_screen",
            audience_disclosure="revealed",
        )
    else:
        item["occurred_at_anchor_business_id"] = anchor.business_id
    return NarrativeEventCandidateCreate(
        **item,
        source_artifact_type=anchor.source_artifact_type,
        source_artifact_business_id=anchor.source_artifact_business_id,
        source_version=anchor.source_version,
        source_hash=anchor.source_hash,
        candidate_evidence=_evidence(
            source_quote,
            strict,
            participant_binding_verified=strict,
            typed_event_ids=typed_event_ids,
        ),
    )


def _anchor(anchors: dict, business_id: str, strict: bool):
    anchor = anchors.get(business_id)
    if anchor is None and strict:
        raise ServiceError(f"记忆候选提取失败：未知来源锚点 {business_id}")
    return anchor or next(iter(anchors.values()))


def _evidence(source_quote: str, strict: bool, **bindings) -> dict:
    evidence = {
        "source_quote": source_quote,
        "source_quote_verified": True,
    }
    if strict:
        evidence.update(
            claim_verified=True,
            claim_mode=bindings.pop("claim_mode", "extractive"),
            verification_version=CLAIM_VERIFICATION_VERSION,
            **bindings,
        )
    return evidence


def _require_typed_event_coverage(
    raw_events: list[dict], expected_events: dict[str, str]
) -> None:
    supplied = [
        event_id
        for item in raw_events
        for event_id in item.get("typed_event_ids") or []
    ]
    if (
        len(raw_events) != len(expected_events)
        or any(len(item.get("typed_event_ids") or []) != 1 for item in raw_events)
        or len(supplied) != len(raw_events)
        or len(set(supplied)) != len(supplied)
        or set(supplied) != set(expected_events)
    ):
        raise ServiceError("记忆候选提取失败：客观事件未逐项覆盖 typed event")


def _semantic(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", value)
