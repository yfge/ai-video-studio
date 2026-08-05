"""Hash-verified v5 interruption and suffix regeneration recovery."""

from app.services.narrative_consistency import (
    freeze_fact_graph,
    validate_chapter_transition,
)
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from fastapi import HTTPException

from .story_novel_chapter_gate import chapter_length_range, non_whitespace_chars
from .story_novel_domain import active_chapters
from .story_novel_sentence_spans import sentence_index_hash, sentence_spans
from .story_novel_v5_plan import valid_v5_plan


def resume_v5_suffix(service, revision, plan_rows):
    plan = revision.generation_plan or {}
    if not valid_v5_plan(plan, revision.story_snapshot or {}):
        raise HTTPException(status_code=409, detail="V5 计划无法通过恢复校验")
    ledger = dict(revision.continuity_ledger or {})
    entries = ledger.get("chapters") or {}
    positions = [int(item["position"]) for item in plan_rows]
    cursor = int(
        ledger.get("stale_from_position")
        or next(
            (
                item
                for item in positions
                if (entries.get(str(item)) or {}).get("status") != "ready"
            ),
            (positions[-1] + 1) if positions else 1,
        )
    )
    graph = validate_v5_chain(revision, plan_rows, stop_before=cursor)
    ledger["current_fact_graph"] = graph
    if cursor > len(positions):
        ledger["state_status"] = "ready"
        ledger.pop("stale_from_position", None)
    else:
        ledger.update(state_status="stale", stale_from_position=cursor)
    revision.continuity_ledger = ledger
    service.db.commit()
    return [item for item in plan_rows if int(item["position"]) >= cursor]


def validate_v5_chain(revision, plan_rows, *, stop_before=None):
    plan = revision.generation_plan or {}
    entries = (revision.continuity_ledger or {}).get("chapters") or {}
    chapters = {item.position: item for item in active_chapters(revision)}
    graph = freeze_fact_graph(plan["consistency_schema"], plan["initial_fact_graph"])
    catalog = {item["id"]: item for item in plan["causal_event_graph"]["events"]}
    for row in plan_rows:
        position = int(row["position"])
        if stop_before is not None and position >= stop_before:
            break
        graph = _validated_prefix_entry(
            plan,
            row,
            entries.get(str(position)) or {},
            chapters.get(position),
            graph,
            catalog,
        )
    return graph


def mark_v5_suffix_stale(revision, from_position):
    ledger = dict(revision.continuity_ledger or {})
    entries = dict(ledger.get("chapters") or {})
    for key, raw in entries.items():
        if int(key) < from_position:
            continue
        entry = dict(raw)
        entry.update(status="stale", stage="stale", extraction_status="stale")
        if int(key) == from_position and entry.get("candidate_attempts"):
            entry["archived_candidate_attempts"] = [
                *(entry.get("archived_candidate_attempts") or []),
                *entry["candidate_attempts"],
            ]
        entries[key] = entry
    ledger.update(
        chapters=entries,
        state_status="stale",
        stale_from_position=min(
            int(ledger.get("stale_from_position") or from_position), from_position
        ),
    )
    ledger.pop("current_fact_graph", None)
    revision.continuity_ledger = ledger


def _validated_prefix_entry(plan, row, entry, chapter, graph, catalog):
    position = int(row["position"])
    sentences = sentence_spans(chapter.content_text) if chapter else []
    minimum, _target, maximum = chapter_length_range(row)
    basic = bool(
        chapter
        and chapter.review_status == "ready"
        and entry.get("status") == "ready"
        and entry.get("body_hash") == chapter.content_hash
        and entry.get("source_hash") == novel_chapter_source_hash(chapter)
        and entry.get("plan_hash") == plan.get("plan_hash")
        and entry.get("schema_hash") == plan.get("consistency_schema_hash")
        and entry.get("snapshot_before_hash") == graph["snapshot_hash"]
        and entry.get("sentence_index_hash") == sentence_index_hash(sentences)
        and entry.get("readability_report", {}).get("status") == "passed"
        and minimum <= non_whitespace_chars(chapter.content_text) <= maximum
    )
    if not basic:
        raise HTTPException(
            status_code=409,
            detail=f"第 {position} 章 ready checkpoint/hash 不完整，拒绝静默重写",
        )
    expected_source = novel_chapter_source_hash(chapter)
    if any(
        item.get("source_artifact_type") != "novel_chapter"
        or item.get("source_artifact_id") != chapter.business_id
        or int(item.get("source_version") or 0) != 1
        or item.get("source_hash") != expected_source
        for item in entry.get("evidence") or []
    ):
        raise HTTPException(
            status_code=409,
            detail=f"第 {position} 章 evidence 来源版本/hash 不匹配",
        )
    delta = {
        "schema": "story_novel_claim_delta.v1",
        "claims": entry.get("claims") or [],
        "perspective_changes": entry.get("perspective_changes") or [],
        "occurred_events": entry.get("events") or [],
        "evidence": entry.get("evidence") or [],
    }
    allowed = {
        item["id"] for item in catalog.values() if item["chapter_position"] == position
    }
    try:
        result = validate_chapter_transition(
            plan["consistency_schema"],
            graph,
            delta,
            sentences,
            allowed_event_ids=allowed,
            event_catalog=catalog,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409, detail=f"第 {position} 章状态补丁无法重放: {exc}"
        ) from exc
    after = result["graph_after"]
    if after["snapshot_hash"] != entry.get("snapshot_after_hash"):
        raise HTTPException(status_code=409, detail=f"第 {position} 章状态 hash 不匹配")
    return after
