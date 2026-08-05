"""Durable continuity.v6 checkpoints for continuous v5 chapter candidates."""

from __future__ import annotations

from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_chapter_gate import non_whitespace_chars
from .story_novel_context_utils import value_hash
from .story_novel_sentence_spans import sentence_index_hash


def checkpoint_scene(service, revision, position, chapter_plan, scene, metrics, before):
    from .story_novel_chapter_service import save_ledger_entry

    entry = _base_entry(revision, position, chapter_plan, before)
    entry.update(
        status="scene_ready",
        stage="scene_planning",
        scene_plan=scene,
        scene_plan_hash=value_hash(scene),
        stage_metrics={"scene_planning": metrics},
    )
    save_ledger_entry(revision, position, entry)
    service.db.commit()
    return entry


def checkpoint_candidate_body(
    service,
    revision,
    position,
    chapter_plan,
    entry,
    content,
    scene,
    *,
    metric_key,
    metric,
):
    from .story_novel_chapter_service import save_ledger_entry

    chapter = service.checkpoint_chapter(
        revision,
        position=position,
        title=chapter_plan["title"],
        content_text=content,
        summary=scene.get("summary"),
        cliffhanger=scene.get("hook"),
        commit=False,
    )
    chapter.review_status = "review_required"
    metrics = dict(entry.get("stage_metrics") or {})
    metrics[metric_key] = metric
    entry.update(
        status="auditing",
        stage="audit",
        chapter_business_id=chapter.business_id,
        body_hash=chapter.content_hash,
        source_hash=novel_chapter_source_hash(chapter),
        char_count=non_whitespace_chars(chapter.content_text),
        stage_metrics=metrics,
        model_call_manifest_hash=value_hash(metrics),
    )
    save_ledger_entry(revision, position, entry)
    service.db.commit()
    return chapter, entry


def finalize_candidate(
    service,
    revision,
    chapter,
    chapter_plan,
    entry,
    selected,
    candidates,
    repair_records,
):
    from .story_novel_chapter_service import (
        save_ledger_entry,
        sync_plan_chapter_runtime,
    )

    passed = _candidate_passed(selected, chapter_plan)
    content = selected["content_text"]
    if chapter.content_text != content:
        chapter = service.checkpoint_chapter(
            revision,
            position=chapter.position,
            title=chapter_plan["title"],
            content_text=content,
            summary=entry["scene_plan"].get("summary"),
            cliffhanger=entry["scene_plan"].get("hook"),
            commit=False,
        )
    chapter.review_status = "ready" if passed else "review_required"
    sentence_index = selected["sentence_index"]
    metrics = _merge_metrics(entry, candidates)
    entry.update(
        {
            "status": "ready" if passed else "review_required",
            "stage": "ready" if passed else "review_required",
            "chapter_business_id": chapter.business_id,
            "body_hash": chapter.content_hash,
            "source_hash": novel_chapter_source_hash(chapter),
            "char_count": non_whitespace_chars(content),
            "content_text": content,
            "sentence_index": sentence_index,
            "sentence_index_hash": sentence_index_hash(sentence_index),
            "claims": selected["claim_delta"].get("claims") or [],
            "events": selected["claim_delta"].get("occurred_events") or [],
            "perspective_changes": selected["claim_delta"].get("perspective_changes")
            or [],
            "evidence": selected["claim_delta"].get("evidence") or [],
            "state_patch": selected.get("state_patch") if passed else None,
            "consistency_report": selected["consistency_report"],
            "readability_report": selected["readability_report"],
            "length_report": selected["length_report"],
            "repair_records": repair_records,
            "candidate_attempts": [_candidate_record(item) for item in candidates],
            "snapshot_after_hash": (
                selected["graph_after"]["snapshot_hash"] if passed else None
            ),
            "snapshot_after": selected["graph_after"] if passed else None,
            "extraction_status": "ready" if passed else "blocked",
            "stage_metrics": metrics,
            "model_call_manifest_hash": value_hash(metrics),
        }
    )
    save_ledger_entry(revision, chapter.position, entry)
    sync_plan_chapter_runtime(revision, chapter.position, entry)
    ledger = dict(revision.continuity_ledger or {})
    if passed:
        ledger.update(
            current_fact_graph=selected["graph_after"],
            state_status="generating",
        )
    else:
        ledger.update(
            state_status="failed",
            stale_from_position=chapter.position,
        )
        revision.continuity_status = "review_required"
    revision.continuity_ledger = ledger
    service.db.commit()
    return chapter, passed


def _base_entry(revision, position, chapter_plan, before):
    plan = revision.generation_plan or {}
    return {
        "schema_hash": plan.get("consistency_schema_hash"),
        "plan_hash": plan.get("plan_hash"),
        "causal_graph_hash": plan.get("causal_graph_hash"),
        "chapter_plan_hash": value_hash(chapter_plan),
        "model_policy_hash": value_hash(plan.get("model_policy") or {}),
        "prompt_policy_hash": (plan.get("prompt_templates") or {}).get("hash"),
        "snapshot_before_hash": before["snapshot_hash"],
    }


def _candidate_passed(candidate, chapter_plan):
    return bool(
        candidate["consistency_report"]["status"] == "passed"
        and candidate["readability_report"]["status"] == "passed"
        and candidate["length_report"]["status"] == "passed"
    )


def _candidate_record(candidate):
    return {
        key: candidate.get(key)
        for key in (
            "attempt_index",
            "attempt_kind",
            "content_text",
            "body_hash",
            "claim_delta",
            "consistency_report",
            "readability_report",
            "length_report",
            "metrics",
        )
    }


def _merge_metrics(entry, candidates):
    result = dict(entry.get("stage_metrics") or {})
    for candidate in candidates:
        for stage, metric in (candidate.get("metrics") or {}).items():
            result.setdefault(f"{stage}.{candidate['attempt_index']}", metric)
    return result
