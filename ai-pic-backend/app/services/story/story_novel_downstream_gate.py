"""Fail-closed validation for Novel Revision -> Episode lineage."""

from __future__ import annotations

from typing import Any, Iterable

from app.schemas.story_novel_export import AdaptationPlanEpisode
from app.services.narrative_memory.source_hash import (
    artifact_hash,
    novel_chapter_source_hash,
)
from fastapi import HTTPException
from pydantic import ValidationError

from .story_novel_domain import active_chapters, materialize_content, sha256_text
from .story_novel_length_service import generation_plan_hash


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


def chapter_source_evidence(chapter) -> dict[str, Any]:
    return {
        "business_id": chapter.business_id,
        "position": chapter.position,
        "title": chapter.title,
        "summary": chapter.summary or chapter.content_text[:500],
        "body_hash": chapter.content_hash,
        "content_hash": chapter.content_hash,
        "source_hash": novel_chapter_source_hash(chapter),
    }


def require_canonical_revision(revision, *, expected_story=None):
    if revision.lifecycle_status != "approved":
        raise _error(
            409,
            "NOVEL_REVISION_NOT_APPROVED",
            "小说修订版尚未审批，不能进入剧集生产",
        )
    story = revision.story
    if expected_story is not None and revision.story_id != expected_story.id:
        raise _error(409, "NOVEL_STORY_MISMATCH", "小说修订版不属于当前 Story")
    if story.canonical_novel_export_id != revision.id:
        raise _error(
            409,
            "NOVEL_REVISION_NOT_CANONICAL",
            "只能使用当前 Story 的 canonical 小说修订版",
        )

    chapters = active_chapters(revision)
    positions = [chapter.position for chapter in chapters]
    if not chapters or positions != list(range(1, len(chapters) + 1)):
        raise _error(
            409,
            "NOVEL_CHAPTERS_INCOMPLETE",
            "canonical 小说章节缺失或顺序不连续",
        )
    if revision.content_hash != sha256_text(materialize_content(revision)):
        raise _error(
            409,
            "NOVEL_CONTENT_HASH_MISMATCH",
            "canonical 小说正文 hash 与当前章节不匹配",
        )

    plan = dict(revision.generation_plan or {})
    if (
        plan.get("status") != "ready"
        or int(plan.get("version") or 0) < 1
        or plan.get("plan_hash") != generation_plan_hash(plan)
    ):
        raise _error(
            409,
            "NOVEL_GENERATION_PLAN_STALE",
            "小说生成计划未就绪，或 plan version/hash 已失效",
        )
    plan_positions = [
        int(row.get("position") or 0) for row in plan.get("chapters") or []
    ]
    if plan_positions != positions:
        raise _error(
            409,
            "NOVEL_GENERATION_PLAN_STALE",
            "小说生成计划未覆盖全部当前有效章节",
        )

    ledger = dict(revision.continuity_ledger or {})
    ledger_rows = ledger.get("chapters") or {}
    invalid = [
        chapter.position
        for chapter in chapters
        if not _chapter_is_ready(chapter, ledger_rows.get(str(chapter.position)) or {})
    ]
    if invalid or ledger.get("state_status") in {"failed", "stale"}:
        raise _error(
            409,
            "NOVEL_CHAPTER_GATE_FAILED",
            f"小说章节 gate/hash/extraction 证据无效: {invalid}",
        )

    report = dict(revision.continuity_report or {})
    coverage = {
        row.get("business_id"): row.get("content_hash")
        for row in report.get("coverage") or []
    }
    expected_coverage = {
        chapter.business_id: chapter.content_hash for chapter in chapters
    }
    if (
        revision.continuity_status != "passed"
        or report.get("status") == "stale"
        or report.get("plan_version") != plan.get("version")
        or report.get("plan_hash") != plan.get("plan_hash")
        or coverage != expected_coverage
    ):
        raise _error(
            409,
            "NOVEL_CONTINUITY_STALE",
            "连续性报告未绑定当前 plan/hash 或未覆盖全部当前章节",
        )
    return plan, chapters


def normalize_episode_rows(
    chapters: Iterable[Any], rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    chapter_ids = {chapter.business_id for chapter in chapters}
    normalized: list[dict[str, Any]] = []
    try:
        for raw in rows:
            item = AdaptationPlanEpisode.model_validate(raw)
            refs = item.source_chapter_business_ids
            if len(refs) != len(set(refs)) or not set(refs).issubset(chapter_ids):
                raise _error(
                    422,
                    "ADAPTATION_PLAN_INVALID_CHAPTERS",
                    "改编计划包含重复、跨 Story 或跨 revision 的章节引用",
                )
            normalized.append(item.model_dump())
    except ValidationError as exc:
        raise _error(
            422,
            "ADAPTATION_PLAN_INVALID",
            f"改编计划结构无效: {exc.errors()[0]['msg']}",
        ) from exc
    numbers = [row["episode_number"] for row in normalized]
    if numbers != list(range(1, len(normalized) + 1)):
        raise _error(
            422,
            "ADAPTATION_PLAN_EPISODE_SEQUENCE_INVALID",
            "集数必须按计划顺序从 1 连续编号",
        )
    covered = {
        chapter_id
        for row in normalized
        for chapter_id in row["source_chapter_business_ids"]
    }
    missing = sorted(chapter_ids - covered)
    if missing:
        raise _error(
            422,
            "ADAPTATION_PLAN_CHAPTER_COVERAGE_INCOMPLETE",
            f"改编计划未覆盖全部当前有效章节: {missing}",
        )
    return normalized


def freeze_adaptation_plan(
    revision, *, version: int, rows: list[dict[str, Any]]
) -> dict[str, Any]:
    generation_plan, chapters = require_canonical_revision(revision)
    if version < 1:
        raise _error(422, "ADAPTATION_PLAN_VERSION_INVALID", "改编计划版本无效")
    plan = {
        "version": version,
        "novel_revision_business_id": revision.business_id,
        "novel_content_hash": revision.content_hash,
        "generation_plan_version": generation_plan["version"],
        "generation_plan_hash": generation_plan["plan_hash"],
        "chapter_sources": [chapter_source_evidence(chapter) for chapter in chapters],
        "episodes": normalize_episode_rows(chapters, rows),
    }
    plan["plan_hash"] = adaptation_plan_hash(plan)
    return plan


def require_adaptation_plan(revision, *, allowed_statuses: set[str] | None = None):
    generation_plan, chapters = require_canonical_revision(revision)
    statuses = allowed_statuses or {"approved", "applied"}
    if revision.adaptation_plan_status not in statuses:
        raise _error(
            409,
            "ADAPTATION_PLAN_NOT_APPROVED",
            "改编计划尚未审批、已过期或已被门禁拒绝",
        )
    plan = dict(revision.adaptation_plan or {})
    expected_sources = [chapter_source_evidence(chapter) for chapter in chapters]
    if (
        int(plan.get("version") or 0) < 1
        or plan.get("novel_revision_business_id") != revision.business_id
        or plan.get("novel_content_hash") != revision.content_hash
        or plan.get("generation_plan_version") != generation_plan.get("version")
        or plan.get("generation_plan_hash") != generation_plan.get("plan_hash")
        or plan.get("chapter_sources") != expected_sources
        or plan.get("plan_hash") != adaptation_plan_hash(plan)
    ):
        raise _error(
            409,
            "ADAPTATION_PLAN_STALE",
            "改编计划 version/hash 或章节来源证据与 canonical 小说不匹配",
        )
    plan["episodes"] = normalize_episode_rows(chapters, plan.get("episodes") or [])
    return plan, chapters


def adaptation_plan_hash(plan: dict[str, Any]) -> str:
    return artifact_hash(
        {
            key: plan.get(key)
            for key in (
                "version",
                "novel_revision_business_id",
                "novel_content_hash",
                "generation_plan_version",
                "generation_plan_hash",
                "chapter_sources",
                "episodes",
            )
        }
    )


def _chapter_is_ready(chapter, entry: dict[str, Any]) -> bool:
    return (
        chapter.review_status in {"ready", "target_changed"}
        and entry.get("status") == "ready"
        and entry.get("extraction_status") == "ready"
        and entry.get("body_hash") == chapter.content_hash
        and entry.get("source_hash") == novel_chapter_source_hash(chapter)
    )
