"""Public chapter workflow plus shared checkpoint/extraction helpers."""

from __future__ import annotations

from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.candidate_verification import (
    verified_novel_candidate,
)
from app.services.narrative_memory.extraction_service import (  # noqa: F401
    NarrativeExtractionService,
)
from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_chapter_gate import non_whitespace_chars, parse_chapter
from .story_novel_plan_versions import (
    is_state_gated_plan,
    is_v3_plan,
    is_v4_plan,
    is_v5_plan,
)

__all__ = [
    "_parse_chapter",
    "generate_or_resume_chapter",
    "non_whitespace_chars",
]


def _parse_chapter(text: str) -> tuple[dict | None, str | None]:
    return parse_chapter(text)


def chapter_entry(revision, position: int) -> dict:
    return dict(
        ((revision.continuity_ledger or {}).get("chapters") or {}).get(str(position))
        or {}
    )


def save_ledger_entry(revision, position: int, entry: dict) -> None:
    ledger = dict(revision.continuity_ledger or {})
    chapters = dict(ledger.get("chapters") or {})
    chapters[str(position)] = entry
    schema = (
        "story_novel_continuity.v6"
        if is_v5_plan(revision.generation_plan)
        else (
            "story_novel_continuity.v5"
            if is_v4_plan(revision.generation_plan)
            else (
                "story_novel_continuity.v4"
                if is_v3_plan(revision.generation_plan)
                else (
                    "story_novel_continuity.v3"
                    if is_state_gated_plan(revision.generation_plan)
                    else "story_novel_continuity.v2"
                )
            )
        )
    )
    ledger.update({"schema": schema, "chapters": chapters})
    revision.continuity_ledger = ledger


def source_candidates(db, revision, chapter) -> tuple[list, list]:
    source_hash = novel_chapter_source_hash(chapter)
    repo = NarrativeMemoryRepository(db)
    entry = chapter_entry(revision, chapter.position)
    require_evidence = is_state_gated_plan(revision.generation_plan)
    events = [
        item
        for item in repo.list_events(revision.story_id)
        if item.status in {"candidate", "approved"}
        and item.source_artifact_business_id == chapter.business_id
        and item.source_hash == source_hash
        and (
            not require_evidence
            or verified_novel_candidate(
                item,
                chapter,
                entry,
                require_ledger_membership=False,
            )
        )
    ]
    memories = [
        item
        for item in repo.list_private_memories(revision.story_id)
        if item.status in {"candidate", "approved"}
        and item.source_artifact_business_id == chapter.business_id
        and item.source_hash == source_hash
        and (
            not require_evidence
            or verified_novel_candidate(
                item,
                chapter,
                entry,
                require_ledger_membership=False,
            )
        )
    ]
    return events, memories


def sync_plan_chapter_runtime(revision, position: int, entry: dict) -> None:
    plan = dict(revision.generation_plan or {})
    if int(plan.get("version") or 0) < 4:
        return
    rows = [dict(item) for item in plan.get("chapters") or []]
    row = next(
        (item for item in rows if int(item.get("position") or 0) == position),
        None,
    )
    if row is None:
        return
    row["actual_chars"] = entry.get("char_count")
    row["generation_status"] = entry.get("status")
    for key in (
        "context_hash",
        "body_hash",
        "source_hash",
        "extraction_status",
        "event_ids",
        "memory_ids",
        "snapshot_before_hash",
        "snapshot_after_hash",
        "readability_status",
    ):
        if key in entry:
            row[key] = entry[key]
    if "event_ids" in entry:
        row["fact_ids"] = entry["event_ids"]
    report = entry.get("readability_report") or {}
    if report:
        row["readability_status"] = report.get("status")
    plan["chapters"] = rows
    revision.generation_plan = plan


async def ensure_chapter_extraction(service, revision, chapter, task=None) -> dict:
    from .story_novel_candidate_checkpoint import (
        ensure_chapter_extraction as ensure_checkpoint,
    )

    return await ensure_checkpoint(service, revision, chapter, task)


def merge_plot_state(revision, position: int, plot_delta: dict) -> None:
    ledger = dict(revision.continuity_ledger or {})
    state = dict(ledger.get("current_state") or {})
    unresolved = list(state.get("unresolved_threads") or [])
    resolved = set(plot_delta.get("resolved_threads") or [])
    unresolved = [item for item in unresolved if item not in resolved]
    for item in plot_delta.get("unresolved_threads") or []:
        if item not in unresolved:
            unresolved.append(item)
    events = list(state.get("key_events") or [])
    events.extend(
        {"chapter": position, "event": item}
        for item in plot_delta.get("key_events") or []
    )
    characters = dict(state.get("character_states") or {})
    characters.update(plot_delta.get("character_states") or {})
    ledger["current_state"] = {
        "key_events": events,
        "unresolved_threads": unresolved,
        "character_states": characters,
    }
    revision.continuity_ledger = ledger


async def generate_or_resume_chapter(
    service,
    revision,
    task,
    chapter_plan: dict,
    generate_text,
    *,
    force: bool = False,
):
    if is_v5_plan(revision.generation_plan):
        from .story_novel_chapter_v5 import generate_or_resume_v5

        return await generate_or_resume_v5(
            service,
            revision,
            task,
            chapter_plan,
            generate_text,
            force=force,
        )
    if is_v4_plan(revision.generation_plan):
        from .story_novel_chapter_v4 import generate_or_resume_v4

        return await generate_or_resume_v4(
            service,
            revision,
            task,
            chapter_plan,
            generate_text,
            force=force,
        )
    if is_v3_plan(revision.generation_plan):
        from .story_novel_chapter_v3 import generate_or_resume_v3

        return await generate_or_resume_v3(
            service,
            revision,
            task,
            chapter_plan,
            generate_text,
            force=force,
        )
    if is_state_gated_plan(revision.generation_plan):
        from .story_novel_chapter_v2 import generate_or_resume_v2

        return await generate_or_resume_v2(
            service,
            revision,
            task,
            chapter_plan,
            generate_text,
            force=force,
        )
    from .story_novel_chapter_legacy import generate_or_resume_legacy

    return await generate_or_resume_legacy(
        service,
        revision,
        task,
        chapter_plan,
        generate_text,
        force=force,
    )
