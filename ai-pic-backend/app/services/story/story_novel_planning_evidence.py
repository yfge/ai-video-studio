"""Deterministic relevance and temporal ranking for chapter planning evidence."""

from __future__ import annotations

import copy


def rank_planning_evidence(
    rows,
    *,
    kind: str,
    chapter_contract: dict,
    canon: dict,
    prior_chapters,
) -> list[dict]:
    positions = {item.business_id: int(item.position) for item in prior_chapters or []}
    relevant_characters = _relevant_character_ids(chapter_contract, canon)
    terms = _contract_terms(chapter_contract)
    ranked = []
    for raw in rows or []:
        item = copy.deepcopy(raw)
        score, reasons = _score(
            item,
            kind=kind,
            relevant_characters=relevant_characters,
            terms=terms,
            source_position=positions.get(item.get("source_chapter_business_id"), 0),
        )
        item["planning_rank"] = {"score": score, "reasons": reasons}
        ranked.append(
            (
                -score,
                -positions.get(item.get("source_chapter_business_id"), 0),
                str(item.get("business_id") or ""),
                item,
            )
        )
    ranked.sort(key=lambda value: value[:3])
    return [item for *_keys, item in ranked]


def _score(item, *, kind, relevant_characters, terms, source_position):
    score, reasons = min(10, max(0, source_position)), []
    if source_position:
        reasons.append("recent_prior_chapter")
    participants = set(item.get("participant_character_ids") or [])
    memory_character = item.get("character_business_id")
    if kind == "world_event" and participants.intersection(relevant_characters):
        score += 20
        reasons.append("chapter_character")
    if kind == "character_memory" and memory_character in relevant_characters:
        score += 24
        reasons.append("chapter_character")
    text = "\n".join(
        str(item.get(key) or "")
        for key in ("summary", "content", "belief", "source_quote")
    )
    matches = [term for term in terms if term and term in text]
    if matches:
        score += min(18, 6 * len(matches))
        reasons.append("chapter_term")
    if item.get("audience_disclosure") == "private":
        score += 2
        reasons.append("knowledge_boundary")
    return score, reasons


def _relevant_character_ids(contract, canon):
    ids = {
        item.get("character_id")
        for item in contract.get("knowledge_grants") or []
        if item.get("character_id")
    }
    ids.update(
        item.get("subject_id")
        for field in ("state_transitions", "location_transitions", "preconditions")
        for item in contract.get(field) or []
        if item.get("subject_id")
    )
    names = set(contract.get("character_focus") or [])
    ids.update(
        item["id"]
        for item in canon.get("entities") or []
        if item.get("kind") == "character" and item.get("name") in names
    )
    return ids


def _contract_terms(contract):
    values = [
        contract.get("goal"),
        *(contract.get("key_events") or []),
        *(contract.get("open_threads") or []),
        *(contract.get("payoffs_due") or []),
    ]
    terms = set()
    for value in values:
        text = str(value or "").strip()
        if text:
            terms.add(text)
        for token in text.replace("，", " ").replace("。", " ").split():
            if len(token) >= 3:
                terms.add(token)
    return sorted(terms)
