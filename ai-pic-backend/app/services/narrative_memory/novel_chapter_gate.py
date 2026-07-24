"""Fail-closed public extraction gate for v2 novel chapters."""

from types import SimpleNamespace

from app.core.exceptions import ConflictError
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story.story_novel_context_utils import prompt_chapter_contract
from app.services.story.story_novel_domain import sha256_text
from app.services.story.story_novel_generation_context import build_chapter_context
from app.services.story.story_novel_length_service import generation_plan_hash
from app.services.story.story_novel_plan_checkpoint import validated_canon_checkpoint
from app.services.story.story_novel_plot_contract import validated_plot_delta
from app.services.story.story_novel_prose_canon_gate import (
    revision_prose_canon_violations,
)
from app.services.story.story_novel_state_service import replay_checkpoint_state
from app.services.story.story_novel_state_validator import validate_state_delta
from fastapi import HTTPException

_GATE_ERROR = "小说章节未通过当前 Canon/状态门禁，不能提取叙事记忆候选"


def require_gated_novel_chapter(db, chapter) -> None:
    plan = dict(chapter.novel_export.generation_plan or {})
    if plan.get("schema") != "story_novel_generation_plan.v2":
        return
    if not _valid_checkpoint(db, chapter, plan):
        raise ConflictError(_GATE_ERROR)


def _valid_checkpoint(db, chapter, plan: dict) -> bool:
    revision = chapter.novel_export
    try:
        canon = validated_canon_checkpoint(plan)
        if (
            not canon
            or plan.get("status") != "ready"
            or plan.get("plan_hash") != generation_plan_hash(plan)
        ):
            return False
        chapter_plan = next(
            item
            for item in plan.get("chapters") or []
            if int(item.get("position") or 0) == chapter.position
        )
        entry = ((revision.continuity_ledger or {}).get("chapters") or {}).get(
            str(chapter.position)
        ) or {}
        context = build_chapter_context(
            SimpleNamespace(db=db), revision, chapter.position, chapter_plan
        )
        evidence = context["evidence"]
        stored_evidence = entry.get("context_evidence") or {}
        state_before = context["state_before"]
        delta = entry.get("state_delta")
        if not isinstance(delta, dict) or not isinstance(state_before, dict):
            return False
        report, state_after = validate_state_delta(
            canon,
            prompt_chapter_contract(chapter_plan),
            state_before,
            delta,
        )
        source_hash = novel_chapter_source_hash(chapter)
        replayed = replay_checkpoint_state(state_before, entry)
        hash_keys = ("canon_hash", "context_hash", "state_before_hash")
        return bool(
            entry.get("status") in {"body_ready", "ready"}
            and entry.get("chapter_business_id") == chapter.business_id
            and chapter.content_hash == sha256_text(chapter.content_text)
            and entry.get("body_hash") == chapter.content_hash
            and entry.get("source_hash") == source_hash
            and all(
                entry.get(key) == evidence.get(key) == stored_evidence.get(key)
                for key in hash_keys
            )
            and report.get("status") == "passed"
            and (entry.get("state_validation") or {}).get("status") == "passed"
            and replayed == state_after
            and entry.get("plot_delta_source") == "typed_state"
            and entry.get("plot_delta_version") == 1
            and entry.get("plot_delta")
            == validated_plot_delta(prompt_chapter_contract(chapter_plan), delta)
            and not revision_prose_canon_violations(
                revision, chapter_plan, chapter.content_text
            )
        )
    except (HTTPException, KeyError, StopIteration, TypeError, ValueError):
        return False
