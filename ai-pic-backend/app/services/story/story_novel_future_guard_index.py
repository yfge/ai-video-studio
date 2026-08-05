"""Compile compact future claims without exposing future chapter prose contracts."""

from __future__ import annotations

import json
import re

from .story_novel_context_utils import prompt_chapter_contract, value_hash

FUTURE_GUARD_SCHEMA = "story_novel_future_guard_index.v1"
_DATE = re.compile(
    r"(?:\d{4}年)?(?:\d{1,2}|[一二三四五六七八九十]{1,3})月"
    r"(?:\d{1,2}|[一二三四五六七八九十]{1,3})日"
)


def compile_future_guard_index(
    chapters: list[dict], milestones=(), entities=()
) -> dict:
    milestone_map = {
        str(item["id"]): item for item in milestones or [] if item.get("id")
    }
    entity_map = {str(item["id"]): item for item in entities or [] if item.get("id")}
    claims = []
    visible_surface = ""
    for chapter in sorted(chapters, key=lambda item: int(item["position"])):
        position = int(chapter["position"])
        events = list(chapter.get("required_event_ids") or [])
        descriptions = list(chapter.get("key_events") or [])
        if len(events) != len(descriptions):
            raise ValueError(f"第 {position} 章事件 ID 与 key_events 不一一对应")
        entity_ids = _unique_strings(
            chapter.get("future_guard_entity_ids") or chapter.get("canon_refs") or [],
            "未来实体",
        )
        for event_id, conclusion in zip(events, descriptions):
            claims.append(
                _claim(
                    claim_id=f"event:{event_id}",
                    kind="event",
                    position=position,
                    conclusion=conclusion,
                    entity_ids=entity_ids,
                    entity_map=entity_map,
                    milestone_id=None,
                    visible_surface=visible_surface,
                )
            )
        for milestone_id in _unique_strings(
            chapter.get("milestones_consumed") or [], "里程碑"
        ):
            milestone = milestone_map.get(milestone_id, {})
            outcome = milestone.get("outcomes", milestone.get("outcome", {}))
            conclusion = json.dumps(
                outcome, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            claims.append(
                _claim(
                    claim_id=f"milestone:{milestone_id}",
                    kind="milestone",
                    position=position,
                    conclusion=conclusion,
                    entity_ids=entity_ids,
                    entity_map=entity_map,
                    milestone_id=milestone_id,
                    visible_surface=visible_surface,
                )
            )
        visible_surface += _compact(
            json.dumps(
                prompt_chapter_contract(chapter), ensure_ascii=False, sort_keys=True
            )
        )
    ids = [item["claim_id"] for item in claims]
    if len(ids) != len(set(ids)):
        raise ValueError("future guard claim ID 重复")
    result = {"schema": FUTURE_GUARD_SCHEMA, "claims": claims}
    result["index_hash"] = value_hash(result)
    return result


def future_guard_index_matches(stored: dict, expected: dict) -> bool:
    """Accept exact indexes or legacy order-only match-term drift."""
    if stored == expected:
        return True
    try:
        payload = dict(stored)
        index_hash = payload.pop("index_hash")
        if index_hash != value_hash(payload) or payload.get("schema") != expected.get(
            "schema"
        ):
            return False
        return _stable_claims(payload["claims"]) == _stable_claims(expected["claims"])
    except (KeyError, TypeError, ValueError):
        return False


def future_claim_cards(
    index: dict,
    position: int,
    content_text: str | None = None,
    claim_ids=(),
    visible_entity_ids=(),
) -> list[dict]:
    if index.get("schema") != FUTURE_GUARD_SCHEMA:
        raise ValueError("future guard index schema 无效")
    requested = set(claim_ids or [])
    if content_text is None and not requested:
        return []
    compact_body = _compact(content_text or "")
    cards = []
    for claim in index.get("claims") or []:
        if int(claim["first_allowed_position"]) <= int(position):
            continue
        explicit = claim["claim_id"] in requested
        matched = _matches(
            compact_body,
            content_text or "",
            claim,
            set(visible_entity_ids or []),
        )
        if explicit or matched:
            cards.append(dict(claim))
    unknown = requested.difference(item["claim_id"] for item in index["claims"])
    if unknown:
        raise ValueError(f"未知 future claim ID: {sorted(unknown)}")
    return cards


def _claim(
    *,
    claim_id: str,
    kind: str,
    position: int,
    conclusion,
    entity_ids,
    entity_map,
    milestone_id,
    visible_surface: str,
) -> dict:
    text = str(conclusion or "").strip()
    if not text:
        raise ValueError(f"future claim 结论为空: {claim_id}")
    dates = sorted(set(_DATE.findall(text)))
    protected_entities = _protected_entities(entity_ids, entity_map)
    entity_terms = sorted(
        {term for entity in protected_entities for term in entity["terms"]}
    )
    payload = {
        "claim_id": claim_id,
        "kind": kind,
        "first_allowed_position": position,
        "protected_entity_ids": list(entity_ids),
        "protected_entity_terms": entity_terms,
        "protected_entities": protected_entities,
        "protected_dates": dates,
        "protected_conclusion": text,
        "match_terms": _claim_match_terms(text, visible_surface),
        "milestone_id": milestone_id,
    }
    payload["claim_fingerprint"] = value_hash(payload)
    return payload


def _matches(
    compact_body: str,
    body: str,
    claim: dict,
    visible_entity_ids: set[str],
) -> bool:
    conclusion = _compact(claim["protected_conclusion"])
    conclusion_without_dates = conclusion
    for date in claim.get("protected_dates") or []:
        conclusion_without_dates = conclusion_without_dates.replace(_compact(date), "")
    if len(conclusion_without_dates) >= 4 and conclusion_without_dates in compact_body:
        return True
    if any(date in body for date in claim.get("protected_dates") or []):
        return True
    terms = [term for term in claim.get("match_terms") or [] if term in compact_body]
    if terms:
        return True
    entity_hits = [
        entity
        for entity in claim.get("protected_entities") or []
        if entity.get("entity_id") not in visible_entity_ids
        if any(_compact(term) in compact_body for term in entity.get("terms") or [])
    ]
    # A hit only selects an audit card; the audit model decides whether the
    # prose actually asserts the future event. Candidate recall is therefore
    # safer than silently omitting a single future character paraphrase.
    return bool(entity_hits)


def _stable_claims(claims) -> list[dict]:
    result = []
    for raw in claims:
        claim = dict(raw)
        fingerprint = claim.pop("claim_fingerprint")
        if fingerprint != value_hash(claim):
            raise ValueError("future claim fingerprint 无效")
        claim.pop("match_terms", None)
        result.append(claim)
    return result


def _protected_entities(entity_ids, entity_map) -> list[dict]:
    result = []
    for entity_id in entity_ids:
        entity = entity_map.get(entity_id) or {}
        terms = sorted(
            {
                str(value).strip()
                for value in [entity.get("name"), *(entity.get("aliases") or [])]
                if str(value or "").strip()
            }
        )
        if terms:
            result.append(
                {"entity_id": entity_id, "kind": entity.get("kind"), "terms": terms}
            )
    return result


def _claim_match_terms(conclusion: str, visible_surface: str) -> list[str]:
    compact = _compact(conclusion)
    matches = []
    for size in (8, 6, 4):
        if len(compact) < size:
            continue
        starts = list(range(0, len(compact) - size + 1, max(2, size // 2)))
        starts.append(len(compact) - size)
        for start in starts:
            term = compact[start : start + size]
            if term in visible_surface or term in matches:
                continue
            matches.append(term)
    return matches


def _compact(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", value)


def _unique_strings(value, label: str) -> list[str]:
    rows = list(value or [])
    if any(not isinstance(item, str) or not item.strip() for item in rows):
        raise ValueError(f"{label}必须使用非空字符串 ID")
    if len(rows) != len(set(rows)):
        raise ValueError(f"{label} ID 重复")
    return rows
