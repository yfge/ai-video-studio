"""Sequential chapter generation, checkpointing, and memory extraction."""

from __future__ import annotations

import re
from typing import Awaitable, Callable

from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.schemas.narrative_extraction import NarrativeExtractionRequest
from app.schemas.story_novel_longform import StoryNovelChapterGeneration
from app.services.narrative_memory.extraction_service import NarrativeExtractionService
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.utils.json_utils import extract_json_block
from fastapi import HTTPException

from .story_novel_ai_prompts import chapter_length_repair_prompt, chapter_prompt
from .story_novel_domain import active_chapters
from .story_novel_generation_context import build_chapter_context
from .story_novel_memory_context import (
    capture_chapter_source_hashes,
    invalidate_chapter_source,
)

GenerateText = Callable[..., Awaitable[str]]
MIN_CHAPTER_CHARS = 3000
MAX_CHAPTER_CHARS = 5000


def non_whitespace_chars(value: str) -> int:
    return len(re.sub(r"\s+", "", value or ""))


def _parse_chapter(text: str) -> tuple[dict | None, str | None]:
    try:
        payload = extract_json_block(text)
        if not payload:
            raise ValueError("missing JSON object")
        if not payload.get("content_text") and payload.get("body"):
            payload = {**payload, "content_text": payload["body"]}
        return StoryNovelChapterGeneration.model_validate(payload).model_dump(), None
    except (ValueError, TypeError) as exc:
        return None, str(exc)


def _chapter_entry(revision, position: int) -> dict:
    return dict(
        ((revision.continuity_ledger or {}).get("chapters") or {}).get(str(position))
        or {}
    )


def _save_ledger_entry(revision, position: int, entry: dict) -> None:
    ledger = dict(revision.continuity_ledger or {})
    chapters = dict(ledger.get("chapters") or {})
    chapters[str(position)] = entry
    ledger.update({"schema": "story_novel_continuity.v2", "chapters": chapters})
    revision.continuity_ledger = ledger


def _source_candidates(db, revision, chapter) -> tuple[list, list]:
    source_hash = novel_chapter_source_hash(chapter)
    repo = NarrativeMemoryRepository(db)
    events = [
        item
        for item in repo.list_events(revision.story_id)
        if item.status in {"candidate", "approved"}
        and item.source_artifact_business_id == chapter.business_id
        and item.source_hash == source_hash
    ]
    memories = [
        item
        for item in repo.list_private_memories(revision.story_id)
        if item.status in {"candidate", "approved"}
        and item.source_artifact_business_id == chapter.business_id
        and item.source_hash == source_hash
    ]
    return events, memories


async def ensure_chapter_extraction(service, revision, chapter) -> dict:
    """Recover extraction without regenerating an already valid chapter body."""
    position = chapter.position
    entry = _chapter_entry(revision, position)
    source_hash = novel_chapter_source_hash(chapter)
    if (
        entry.get("extraction_status") == "ready"
        and entry.get("source_hash") == source_hash
    ):
        return entry
    events, memories = _source_candidates(service.db, revision, chapter)
    if not events and not memories:
        await NarrativeExtractionService(NarrativeMemoryRepository(service.db)).extract(
            revision.story,
            NarrativeExtractionRequest(
                source_scope="novel_chapter",
                source_artifact_business_id=chapter.business_id,
                model=revision.model,
            ),
            service.user,
        )
        events, memories = _source_candidates(service.db, revision, chapter)
    entry.update(
        {
            "status": "ready",
            "body_hash": chapter.content_hash,
            "source_hash": source_hash,
            "extraction_status": "ready",
            "event_ids": [item.business_id for item in events],
            "memory_ids": [item.business_id for item in memories],
        }
    )
    _save_ledger_entry(revision, position, entry)
    service.db.commit()
    return entry


def _merge_plot_state(revision, position: int, plot_delta: dict) -> None:
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
    generate_text: GenerateText,
    *,
    force: bool = False,
):
    position = int(chapter_plan["position"])
    existing = next(
        (item for item in active_chapters(revision) if item.position == position), None
    )
    context_pack = build_chapter_context(service, revision, position, chapter_plan)
    evidence = context_pack["evidence"]
    entry = _chapter_entry(revision, position)
    valid_body = (
        existing
        and MIN_CHAPTER_CHARS
        <= non_whitespace_chars(existing.content_text)
        <= MAX_CHAPTER_CHARS
    )
    context_matches = entry.get("context_hash") == evidence["context_hash"]
    if valid_body and context_matches and not force:
        task.description = f"第 {position} 章正文有效，正在校验事实与记忆…"
        service.db.commit()
        await ensure_chapter_extraction(service, revision, existing)
        return existing

    old_source = (
        capture_chapter_source_hashes([existing])[existing.business_id]
        if existing
        else None
    )
    target_chars = int(chapter_plan["target_chars"])
    task.description = f"正在生成第 {position}/{revision.chapter_count} 章…"
    service.db.commit()
    text = await generate_text(
        revision,
        chapter_prompt(context_pack=context_pack["context"], target_chars=target_chars),
        max_tokens=min(16000, max(9000, target_chars * 3)),
    )
    result, parse_error = _parse_chapter(text)
    actual_chars = non_whitespace_chars((result or {}).get("content_text", ""))
    if not result or not MIN_CHAPTER_CHARS <= actual_chars <= MAX_CHAPTER_CHARS:
        prior = result or {"raw": text[:8000], "validation_error": parse_error}
        repaired = await generate_text(
            revision,
            chapter_length_repair_prompt(
                context_pack=context_pack["context"],
                prior_result=prior,
                actual_chars=actual_chars,
                target_chars=target_chars,
            ),
            max_tokens=min(16000, max(9000, target_chars * 3)),
        )
        result, parse_error = _parse_chapter(repaired)
        actual_chars = non_whitespace_chars((result or {}).get("content_text", ""))
    if not result or not MIN_CHAPTER_CHARS <= actual_chars <= MAX_CHAPTER_CHARS:
        raise HTTPException(
            status_code=500,
            detail=f"第 {position} 章长度门禁失败：{actual_chars} 个非空白字符",
        )

    chapter = service.checkpoint_chapter(
        revision,
        position=position,
        title=result["title"],
        content_text=result["content_text"],
        summary=result["summary"],
        cliffhanger=result.get("cliffhanger"),
    )
    if old_source:
        invalidate_chapter_source(service.db, revision, chapter, old_source)
    _save_ledger_entry(
        revision,
        position,
        {
            "status": "body_ready",
            "chapter_business_id": chapter.business_id,
            "body_hash": chapter.content_hash,
            "source_hash": novel_chapter_source_hash(chapter),
            "char_count": actual_chars,
            "context_hash": evidence["context_hash"],
            "context_evidence": evidence,
            "plot_delta": result["plot_delta"],
            "extraction_status": "pending",
        },
    )
    _merge_plot_state(revision, position, result["plot_delta"])
    service.db.commit()
    await ensure_chapter_extraction(service, revision, chapter)
    return chapter
