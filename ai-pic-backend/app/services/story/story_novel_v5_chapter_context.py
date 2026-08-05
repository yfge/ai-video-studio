"""Pure context and resume helpers for one v5 chapter."""

from app.services.narrative_consistency import freeze_fact_graph
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from fastapi import HTTPException

from .story_novel_chapter_gate import chapter_length_range
from .story_novel_chapter_service import chapter_entry
from .story_novel_context_utils import value_hash
from .story_novel_domain import compact_chapter_context
from .story_novel_v5_readability import repair_span
from .story_novel_v5_text import neighbor_context


def snapshot_before(revision, position, plan):
    schema = plan["consistency_schema"]
    if position == 1:
        return freeze_fact_graph(schema, plan["initial_fact_graph"])
    prior = chapter_entry(revision, position - 1)
    if prior.get("status") != "ready" or not prior.get("snapshot_after"):
        raise HTTPException(
            status_code=409, detail=f"第 {position - 1} 章状态快照未就绪"
        )
    graph = freeze_fact_graph(schema, prior["snapshot_after"])
    if graph["snapshot_hash"] != prior.get("snapshot_after_hash"):
        raise HTTPException(
            status_code=409, detail=f"第 {position - 1} 章状态 hash 不匹配"
        )
    return graph


def chapter_contract(chapter, before, scene, plan):
    catalog = plan["causal_event_graph"]["events"]
    allowed = [
        item for item in catalog if item["chapter_position"] == chapter["position"]
    ]
    obligations = [
        item
        for item in plan["causal_event_graph"].get("obligations") or []
        if item["chapter_position"] == chapter["position"]
    ]
    return {
        "schema": plan["consistency_schema"],
        "snapshot_before": before,
        "event_catalog": catalog,
        "allowed_events": allowed,
        "obligations": obligations,
        "chapter": chapter,
        "scene_plan": scene,
    }


def scene_input(revision, chapter, before, plan):
    contract = chapter_contract(chapter, before, {}, plan)
    return {
        **_model_contract(contract),
        "recent_chapters": compact_chapter_context(revision, chapter["position"]),
    }


def prose_input(revision, contract):
    snapshot = revision.story_snapshot or {}
    minimum, target, maximum = chapter_length_range(contract["chapter"])
    return {
        **_model_contract(contract),
        "story_style": {
            key: snapshot.get(key)
            for key in ("title", "genre", "theme", "target_audience")
        },
        "recent_chapters": compact_chapter_context(
            revision, contract["chapter"]["position"]
        ),
        "min_chars": minimum,
        "target_chars": target,
        "max_chars": maximum,
    }


def _model_contract(contract):
    return {
        "schema": contract["schema"],
        "snapshot_before": prompt_snapshot(contract["snapshot_before"]),
        "allowed_events": contract["allowed_events"],
        "obligations": contract["obligations"],
        "chapter": contract["chapter"],
        "scene_plan": contract["scene_plan"],
    }


def prompt_snapshot(snapshot):
    return {
        key: snapshot.get(key)
        for key in (
            "schema",
            "entities",
            "facts",
            "occurred_event_ids",
            "snapshot_hash",
        )
    }


def repair_sentence_ids(candidate):
    spans = []
    readability = repair_span(
        candidate["readability_report"], candidate["sentence_index"]
    )
    if readability:
        spans.append(readability)
    spans.extend(
        item.get("sentence_ids") or []
        for item in candidate["consistency_report"].get("issues") or []
        if item.get("sentence_ids")
    )
    order = {
        item["sentence_id"]: index
        for index, item in enumerate(candidate["sentence_index"])
    }
    return min(spans, key=lambda ids: (len(ids), order[ids[0]])) if spans else []


def span_input(contract, candidate, sentence_ids):
    issues = [
        item
        for item in candidate["readability_report"].get("issues") or []
        if set(item.get("sentence_ids") or []) & set(sentence_ids)
    ]
    return {
        **neighbor_context(candidate["content_text"], sentence_ids),
        "issues": issues or candidate["consistency_report"].get("issues") or [],
        "allowed_events": contract["allowed_events"],
        "snapshot_before_hash": contract["snapshot_before"]["snapshot_hash"],
    }


def rewrite_input(revision, contract, candidate):
    value = prose_input(revision, contract)
    value["readability_failures"] = {
        "dimensions": candidate["readability_report"].get("failing_dimension_ids"),
        "issues": candidate["readability_report"].get("issues"),
    }
    return value


def entry_identity(revision, chapter, before):
    plan = revision.generation_plan or {}
    return {
        "schema_hash": plan.get("consistency_schema_hash"),
        "plan_hash": plan.get("plan_hash"),
        "chapter_plan_hash": value_hash(chapter),
        "snapshot_before_hash": before["snapshot_hash"],
    }


def reusable_chapter(chapter, entry, plan, before):
    return bool(
        chapter
        and chapter.review_status == "ready"
        and entry.get("status") == "ready"
        and entry.get("body_hash") == chapter.content_hash
        and entry.get("plan_hash") == plan.get("plan_hash")
        and entry.get("schema_hash") == plan.get("consistency_schema_hash")
        and entry.get("snapshot_before_hash") == before["snapshot_hash"]
        and entry.get("snapshot_after_hash")
    )


def reusable_audit_body(chapter, entry, plan, before):
    return bool(
        chapter
        and entry.get("status") == "auditing"
        and entry.get("body_hash") == chapter.content_hash
        and entry.get("source_hash") == novel_chapter_source_hash(chapter)
        and entry.get("plan_hash") == plan.get("plan_hash")
        and entry.get("schema_hash") == plan.get("consistency_schema_hash")
        and entry.get("snapshot_before_hash") == before["snapshot_hash"]
    )
