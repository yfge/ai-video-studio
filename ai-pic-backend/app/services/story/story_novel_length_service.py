"""Length profiles and deterministic generation-plan materialization."""

from __future__ import annotations

from app.schemas.story_novel_export import (
    NovelLengthRange,
    StoryNovelCreateRevisionRequest,
)
from fastapi import HTTPException

from . import story_novel_model_policy as model_policy
from .story_novel_chapter_gate import non_whitespace_chars
from .story_novel_length_contract import content_hash as _content_hash
from .story_novel_length_contract import normalize_overrides as _normalize_overrides
from .story_novel_length_contract import resolve_profile as _resolve_profile
from .story_novel_length_contract import validate_model_capacity
from .story_novel_length_outline import confirmed_outline as _confirmed_outline
from .story_novel_plan_hash import generation_plan_hash


def build_length_plan(
    story,
    request: StoryNovelCreateRevisionRequest,
    *,
    version: int = 4,
) -> dict:
    outline, chapters, positions = _confirmed_outline(story)
    if request.model_policy is not None:
        _require_v4_seed_contract(story, outline)
    profile = _resolve_profile(request.length_profile_id, request.custom_length_profile)
    overrides = _normalize_overrides(request.chapter_length_overrides, positions)
    planned = _apply_ranges(chapters, profile, overrides)
    resolved_policy = model_policy.resolve_creation_model_policy(story, request)
    validate_model_capacity(
        resolved_policy["prose_model"], max(row["max_chars"] for row in planned)
    )
    outline_hash = _content_hash(outline)
    plan = {
        "schema": model_policy.generation_plan_schema(request),
        "version": version,
        "status": "ready",
        "phase": "spec_ready",
        "story_seed_version": int(story.story_seed_version or 1),
        "outline_hash": outline_hash,
        "model": resolved_policy["prose_model"],
        "model_policy": resolved_policy,
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


def _require_v4_seed_contract(story, outline: dict) -> None:
    required = (
        "progression_arcs",
        "core_character_routes",
        "scope_taxonomy",
        "initial_scope_nodes",
    )
    valid_versions = (
        int(outline.get("planning_structure_version") or 0) == 1
        and int(outline.get("roadmap_version") or 0) == 1
    )
    if not valid_versions or any(not outline.get(key) for key in required):
        raise HTTPException(
            status_code=409,
            detail="v4 小说版本需要完整的分卷 Roadmap、核心人物路线与初始世界范围",
        )
    protagonists = {
        str(item.get("virtual_ip_business_id") or "")
        for item in (story.story_seed or {}).get("protagonists") or []
    }
    routed = {
        str(item.get("character_ref") or "")
        for item in outline.get("core_character_routes") or []
    }
    missing = sorted(item for item in protagonists - routed if item)
    if not protagonists or missing:
        raise HTTPException(
            status_code=409,
            detail=f"v4 核心人物路线未覆盖 StorySeed 主角: {missing}",
        )


def apply_length_spec(revision, request) -> dict:
    current = dict(revision.generation_plan or {})
    expected = int(request.expected_plan_version)
    frozen_rows, positions = _validate_frozen_spec(revision, current, expected)
    profile = _resolve_profile(request.length_profile_id, request.custom_length_profile)
    overrides = _normalize_overrides(request.chapter_length_overrides, positions)
    frozen_rows = _apply_ranges(frozen_rows, profile, overrides)
    resolved_policy, model_changed = model_policy.resolve_updated_model_policy(
        revision, current, request
    )
    model = resolved_policy["prose_model"]
    validate_model_capacity(model, max(row["max_chars"] for row in frozen_rows))
    revision.model = model
    serialized_overrides = {
        str(position): value.model_dump() for position, value in overrides.items()
    }
    if (
        current.get("length_profile") == profile
        and (current.get("chapter_length_overrides") or {}) == serialized_overrides
        and not model_changed
    ):
        return current
    plan = {
        **current,
        "version": expected + 1,
        "model": model,
        "model_policy": resolved_policy,
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
    plan_row.update({"fact_ids": entry["event_ids"]} if "event_ids" in entry else {})
