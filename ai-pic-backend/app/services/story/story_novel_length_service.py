"""Length profiles and deterministic generation-plan materialization."""

from __future__ import annotations

from app.schemas.story_novel_export import (
    NovelLengthRange,
    StoryNovelCreateRevisionRequest,
)
from fastapi import HTTPException

from .story_novel_chapter_gate import non_whitespace_chars
from .story_novel_length_contract import content_hash as _content_hash
from .story_novel_length_contract import normalize_overrides as _normalize_overrides
from .story_novel_length_contract import resolve_profile as _resolve_profile
from .story_novel_length_contract import validate_model_capacity
from .story_novel_length_outline import confirmed_outline as _confirmed_outline


def build_length_plan(
    story,
    request: StoryNovelCreateRevisionRequest,
    *,
    version: int = 4,
) -> dict:
    outline, chapters, positions = _confirmed_outline(story)
    profile = _resolve_profile(request.length_profile_id, request.custom_length_profile)
    overrides = _normalize_overrides(request.chapter_length_overrides, positions)
    planned = _apply_ranges(chapters, profile, overrides)
    validate_model_capacity(request.model, max(row["max_chars"] for row in planned))
    outline_hash = _content_hash(outline)
    plan = {
        "schema": "story_novel_generation_plan.v2",
        "version": version,
        "status": "ready",
        "phase": "spec_ready",
        "story_seed_version": int(story.story_seed_version or 1),
        "outline_hash": outline_hash,
        "length_profile": profile,
        "chapter_length_overrides": {
            str(position): value.model_dump() for position, value in overrides.items()
        },
        "chapter_count": len(planned),
        "planned_min_chars": sum(row["min_chars"] for row in planned),
        "planned_target_chars": sum(row["target_chars"] for row in planned),
        "planned_max_chars": sum(row["max_chars"] for row in planned),
        "chapters": planned,
    }
    if int(outline.get("thread_schedule_version") or 0) == 1:
        payoffs = list(outline.get("thread_payoffs") or [])
        plan.update(
            {
                "thread_payoffs": payoffs,
                "thread_payoffs_hash": _content_hash(payoffs),
                "thread_payoffs_outline_hash": outline_hash,
            }
        )
    plan["plan_hash"] = generation_plan_hash(plan)
    return plan


def apply_length_spec(revision, request) -> dict:
    current = dict(revision.generation_plan or {})
    expected = int(request.expected_plan_version)
    frozen_rows, positions = _validate_frozen_spec(revision, current, expected)
    profile = _resolve_profile(request.length_profile_id, request.custom_length_profile)
    overrides = _normalize_overrides(request.chapter_length_overrides, positions)
    frozen_rows = _apply_ranges(frozen_rows, profile, overrides)
    model = request.model if "model" in request.model_fields_set else revision.model
    validate_model_capacity(model, max(row["max_chars"] for row in frozen_rows))
    revision.model = model
    serialized_overrides = {
        str(position): value.model_dump() for position, value in overrides.items()
    }
    if (
        current.get("length_profile") == profile
        and (current.get("chapter_length_overrides") or {}) == serialized_overrides
    ):
        return current
    plan = {
        **current,
        "version": expected + 1,
        "length_profile": profile,
        "chapter_length_overrides": serialized_overrides,
        "planned_min_chars": sum(row["min_chars"] for row in frozen_rows),
        "planned_target_chars": sum(row["target_chars"] for row in frozen_rows),
        "planned_max_chars": sum(row["max_chars"] for row in frozen_rows),
        "chapters": frozen_rows,
    }
    _refresh_existing_lengths(revision, plan)
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.continuity_status = "review_required"
    _mark_report_stale(revision, plan["version"])
    return plan


def _apply_ranges(chapters, profile, overrides) -> list[dict]:
    planned = []
    for source in chapters:
        position = int(source["position"])
        length = overrides.get(position) or NovelLengthRange(
            min_chars=profile["default_min_chars"],
            target_chars=profile["default_target_chars"],
            max_chars=profile["default_max_chars"],
        )
        length_source = (
            "chapter_override" if position in overrides else "profile_default"
        )
        planned.append(
            {
                **source,
                **length.model_dump(),
                "length_source": length_source,
                "length": {**length.model_dump(), "source": length_source},
            }
        )
    return planned


def _validate_frozen_spec(revision, current, expected) -> tuple[list[dict], list[int]]:
    if int(current.get("version") or 0) != expected:
        raise HTTPException(status_code=409, detail="生成计划版本已变化，请刷新后重试")
    snapshot = revision.story_snapshot or {}
    outline = (snapshot.get("story_seed") or {}).get("structured_outline") or {}
    if int(current.get("story_seed_version") or 0) != int(
        snapshot.get("story_seed_version") or 0
    ) or current.get("outline_hash") != _content_hash(outline):
        raise HTTPException(status_code=409, detail="冻结大纲与当前生成计划不匹配")
    rows = [dict(item) for item in current.get("chapters") or []]
    positions = [int(item.get("position") or 0) for item in rows]
    if positions != list(range(1, len(rows) + 1)):
        raise HTTPException(status_code=409, detail="冻结章节计划不连续")
    return rows, positions


def _refresh_existing_lengths(revision, plan) -> None:
    for chapter in revision.chapters or []:
        row = next(
            (
                item
                for item in plan["chapters"]
                if int(item["position"]) == chapter.position
            ),
            None,
        )
        if not row or not chapter.content_text:
            continue
        actual = non_whitespace_chars(chapter.content_text)
        chapter.review_status = (
            "target_changed"
            if row["min_chars"] <= actual <= row["max_chars"]
            else "length_mismatch"
        )
        ledger = dict(revision.continuity_ledger or {})
        entries = dict(ledger.get("chapters") or {})
        entry = dict(entries.get(str(chapter.position)) or {})
        entry["length_status"] = chapter.review_status
        entry["char_count"] = actual
        entries[str(chapter.position)] = entry
        ledger["chapters"] = entries
        revision.continuity_ledger = ledger
        row["actual_chars"] = actual
        _mirror_ledger_fields(row, entry)


def _mark_report_stale(revision, plan_version: int) -> None:
    if revision.continuity_report:
        report = dict(revision.continuity_report)
        report.pop("report_hash", None)
        report.update(
            {
                "status": "stale",
                "stale_reason": "length_spec_changed",
                "stale_for_plan_version": plan_version,
            }
        )
        report["report_hash"] = _content_hash(report)
        revision.continuity_report = report


def generation_plan_hash(plan: dict) -> str:
    chapter_keys = (
        "position",
        "title",
        "goal",
        "key_events",
        "character_focus",
        "open_threads",
        "end_state",
        "min_chars",
        "target_chars",
        "max_chars",
        "length_source",
        "preconditions",
        "required_event_ids",
        "state_transitions",
        "knowledge_grants",
        "location_transitions",
        "milestones_consumed",
        "forbidden_event_ids",
        "payoffs_due",
        "canon_refs",
        "timeline_event_bindings",
    )
    contract = {
        "schema": plan.get("schema"),
        "version": plan.get("version"),
        "story_seed_version": plan.get("story_seed_version"),
        "outline_hash": plan.get("outline_hash"),
        "canon_hash": plan.get("canon_hash"),
        "canon_gate_version": plan.get("canon_gate_version"),
        "thread_payoffs_hash": plan.get("thread_payoffs_hash"),
        "thread_payoffs_outline_hash": plan.get("thread_payoffs_outline_hash"),
        "length_profile": plan.get("length_profile"),
        "chapter_length_overrides": plan.get("chapter_length_overrides"),
        "chapters": [
            {key: row.get(key) for key in chapter_keys}
            for row in plan.get("chapters") or []
        ],
    }
    return _content_hash(contract)


def _mirror_ledger_fields(plan_row: dict, entry: dict) -> None:
    for key in (
        "context_hash",
        "body_hash",
        "source_hash",
        "extraction_status",
        "event_ids",
        "memory_ids",
    ):
        if key in entry:
            plan_row[key] = entry[key]
    if "event_ids" in entry:
        plan_row["fact_ids"] = entry["event_ids"]
