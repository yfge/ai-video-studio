"""Continuous-prose chapter orchestration for topic-neutral v5 plans."""

from __future__ import annotations

from fastapi import HTTPException

from .story_novel_chapter_service import chapter_entry
from .story_novel_context_utils import value_hash
from .story_novel_domain import active_chapters
from .story_novel_v5_checkpoint import (
    checkpoint_candidate_body,
    checkpoint_scene,
    finalize_candidate,
)
from .story_novel_v5_generation import (
    generate_full_rewrite,
    generate_prose,
    generate_scene,
    generate_span_repair,
)
from .story_novel_v5_candidate import candidate_passed, evaluate_candidate
from .story_novel_v5_chapter_context import (
    chapter_contract,
    entry_identity,
    prose_input,
    repair_sentence_ids,
    reusable_audit_body,
    reusable_chapter,
    rewrite_input,
    scene_input,
    snapshot_before,
    span_input,
)
from .story_novel_v5_plan import valid_v5_plan
from .story_novel_v5_readability import candidate_rank
from .story_novel_v5_text import replace_span


async def generate_or_resume_v5(
    service, revision, task, chapter_plan: dict, generate_text, *, force=False
):
    plan = dict(revision.generation_plan or {})
    if not valid_v5_plan(plan, revision.story_snapshot or {}):
        raise HTTPException(status_code=409, detail="V5 生成计划或 hash 无效")
    position = int(chapter_plan["position"])
    existing = next(
        (item for item in active_chapters(revision) if item.position == position), None
    )
    entry = chapter_entry(revision, position)
    before = snapshot_before(revision, position, plan)
    if not force and reusable_chapter(existing, entry, plan, before):
        return existing
    scene, entry = await _scene_for(
        service,
        revision,
        task,
        chapter_plan,
        entry,
        before,
        plan,
        generate_text,
    )
    contract = chapter_contract(chapter_plan, before, scene, plan)
    if reusable_audit_body(existing, entry, plan, before):
        chapter, prose = existing, existing.content_text
        candidate_metrics = {}
        task.description = f"第 {position}/{revision.chapter_count} 章：恢复正文抽取"
    else:
        task.description = f"第 {position}/{revision.chapter_count} 章：生成连续正文"
        prose, prose_metrics = await generate_prose(
            revision, position, prose_input(revision, contract), generate_text
        )
        chapter, entry = checkpoint_candidate_body(
            service,
            revision,
            position,
            chapter_plan,
            entry,
            prose,
            scene,
            metric_key="prose.0",
            metric=prose_metrics,
        )
        candidate_metrics = {"prose": prose_metrics}
    candidates = [
        await evaluate_candidate(
            revision,
            position,
            chapter,
            contract,
            prose,
            generate_text,
            0,
            "initial",
            candidate_metrics,
        )
    ]
    repairs = []
    if not candidate_passed(candidates[-1]):
        span = repair_sentence_ids(candidates[-1])
        if span:
            task.description = (
                f"第 {position}/{revision.chapter_count} 章：局部句段返修"
            )
            repaired, repair_metrics = await generate_span_repair(
                revision,
                position,
                span_input(contract, candidates[-1], span),
                generate_text,
            )
            content = replace_span(prose, span, repaired)
            chapter, entry = checkpoint_candidate_body(
                service,
                revision,
                position,
                chapter_plan,
                entry,
                content,
                scene,
                metric_key="span_repair.1",
                metric=repair_metrics,
            )
            candidates.append(
                await evaluate_candidate(
                    revision,
                    position,
                    chapter,
                    contract,
                    content,
                    generate_text,
                    1,
                    "span_repair",
                    {"span_repair": repair_metrics},
                )
            )
            repairs.append({"kind": "sentence_span", "sentence_ids": span})
    rewrite_source = next(
        (
            item
            for item in reversed(candidates)
            if item["consistency_report"]["status"] == "passed"
            and item["readability_report"]["status"] == "failed"
        ),
        None,
    )
    if rewrite_source:
        task.description = f"第 {position}/{revision.chapter_count} 章：整章重写"
        rewritten, rewrite_metrics = await generate_full_rewrite(
            revision,
            position,
            rewrite_input(revision, contract, rewrite_source),
            generate_text,
        )
        chapter, entry = checkpoint_candidate_body(
            service,
            revision,
            position,
            chapter_plan,
            entry,
            rewritten,
            scene,
            metric_key="full_rewrite.2",
            metric=rewrite_metrics,
        )
        candidates.append(
            await evaluate_candidate(
                revision,
                position,
                chapter,
                contract,
                rewritten,
                generate_text,
                2,
                "full_rewrite",
                {"full_rewrite": rewrite_metrics},
            )
        )
        repairs.append({"kind": "full_rewrite", "read_old_body": False})
    selected = max(candidates, key=candidate_rank)
    chapter, passed = finalize_candidate(
        service,
        revision,
        chapter,
        chapter_plan,
        entry,
        selected,
        candidates,
        repairs,
    )
    if not passed:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "V5_CHAPTER_REVIEW_REQUIRED",
                "position": position,
                "consistency": selected["consistency_report"],
                "readability": selected["readability_report"],
                "length": selected["length_report"],
            },
        )
    return chapter


async def _scene_for(
    service, revision, task, chapter_plan, entry, before, plan, generate_text
):
    expected = entry_identity(revision, chapter_plan, before)
    if (
        entry.get("scene_plan")
        and entry.get("scene_plan_hash") == value_hash(entry["scene_plan"])
        and all(entry.get(key) == value for key, value in expected.items())
    ):
        return entry["scene_plan"], entry
    position = int(chapter_plan["position"])
    task.description = f"第 {position}/{revision.chapter_count} 章：规划场景"
    value = scene_input(revision, chapter_plan, before, plan)
    scene, metrics = await generate_scene(revision, position, value, generate_text)
    entry = checkpoint_scene(
        service, revision, position, chapter_plan, scene, metrics, before
    )
    return scene, entry
