"""Compatibility path for generation-plan v1 novel revisions."""

from __future__ import annotations

from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from fastapi import HTTPException

from .story_novel_ai_prompts import chapter_length_repair_prompt, chapter_prompt
from .story_novel_chapter_gate import (
    chapter_length_range,
    chapter_output_tokens,
    non_whitespace_chars,
    parse_chapter,
)
from .story_novel_domain import active_chapters
from .story_novel_generation_context import build_chapter_context
from .story_novel_memory_context import (
    capture_chapter_source_hashes,
    invalidate_chapter_source,
)


async def generate_or_resume_legacy(
    service,
    revision,
    task,
    chapter_plan: dict,
    generate_text,
    *,
    force: bool = False,
):
    from .story_novel_chapter_service import chapter_entry
    from .story_novel_task_guard import ensure_task_not_cancelled

    position = int(chapter_plan["position"])
    existing = next(
        (item for item in active_chapters(revision) if item.position == position), None
    )
    context_pack = build_chapter_context(service, revision, position, chapter_plan)
    if await _resume_existing(
        service,
        revision,
        task,
        existing,
        chapter_entry(revision, position),
        context_pack["evidence"],
        chapter_plan,
        force,
    ):
        return existing
    old_source = (
        capture_chapter_source_hashes([existing])[existing.business_id]
        if existing
        else None
    )
    task.description = f"正在生成第 {position}/{revision.chapter_count} 章…"
    service.db.commit()
    result, actual_chars = await _generate_valid_body(
        revision, chapter_plan, context_pack["context"], generate_text
    )
    ensure_task_not_cancelled(service.db, task)
    return await _checkpoint_body(
        service,
        revision,
        task,
        position,
        result,
        actual_chars,
        context_pack["evidence"],
        old_source,
    )


async def _resume_existing(
    service, revision, task, existing, entry, evidence, plan, force
):
    from .story_novel_chapter_service import ensure_chapter_extraction

    minimum, _target, maximum = chapter_length_range(plan)
    reusable = (
        existing
        and minimum <= non_whitespace_chars(existing.content_text) <= maximum
        and entry.get("context_hash") == evidence["context_hash"]
        and not force
    )
    if not reusable:
        return False
    task.description = f"第 {existing.position} 章正文有效，正在校验事实与记忆…"
    service.db.commit()
    await ensure_chapter_extraction(service, revision, existing, task)
    return True


async def _generate_valid_body(revision, plan, context, generate_text):
    minimum, target, maximum = chapter_length_range(plan)
    text = await generate_text(
        revision,
        chapter_prompt(
            context_pack=context,
            min_chars=minimum,
            target_chars=target,
            max_chars=maximum,
        ),
        max_tokens=chapter_output_tokens(plan),
    )
    result, parse_error = parse_chapter(text)
    actual = non_whitespace_chars((result or {}).get("content_text", ""))
    if not result or not minimum <= actual <= maximum:
        prior = result or {"raw": text[:8000], "validation_error": parse_error}
        text = await generate_text(
            revision,
            chapter_length_repair_prompt(
                context_pack=context,
                prior_result=prior,
                actual_chars=actual,
                target_chars=target,
                min_chars=minimum,
                max_chars=maximum,
            ),
            max_tokens=chapter_output_tokens(plan),
        )
        result, _error = parse_chapter(text)
        actual = non_whitespace_chars((result or {}).get("content_text", ""))
    if not result or not minimum <= actual <= maximum:
        raise HTTPException(
            status_code=500,
            detail=(
                f"章节长度门禁失败：计划范围 {minimum}–{maximum}，"
                f"实际 {actual} 个非空白字符。已完成章节已保留，可从本章恢复"
            ),
        )
    return result, actual


async def _checkpoint_body(
    service, revision, task, position, result, actual, evidence, old_source
):
    from .story_novel_chapter_service import (
        ensure_chapter_extraction,
        merge_plot_state,
        save_ledger_entry,
        sync_plan_chapter_runtime,
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
    entry = {
        "status": "body_ready",
        "chapter_business_id": chapter.business_id,
        "body_hash": chapter.content_hash,
        "source_hash": novel_chapter_source_hash(chapter),
        "char_count": actual,
        "context_hash": evidence["context_hash"],
        "context_evidence": evidence,
        "plot_delta": result["plot_delta"],
        "extraction_status": "pending",
    }
    save_ledger_entry(revision, position, entry)
    sync_plan_chapter_runtime(revision, position, entry)
    merge_plot_state(revision, position, result["plot_delta"])
    service.db.commit()
    await ensure_chapter_extraction(service, revision, chapter, task)
    return chapter
