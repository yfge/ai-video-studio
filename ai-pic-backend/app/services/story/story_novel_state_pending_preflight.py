"""Pure preflight for extraction-only recovery of a saved chapter body."""

from __future__ import annotations

from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_chapter_gate import chapter_length_range, non_whitespace_chars
from .story_novel_context_utils import prompt_chapter_contract
from .story_novel_domain import sha256_text
from .story_novel_evidence_rules import required_event_anchor_violations
from .story_novel_gate_support import premature_plan_violations
from .story_novel_length_service import generation_plan_hash
from .story_novel_plan_checkpoint import validated_canon_checkpoint
from .story_novel_prose_canon_gate import revision_prose_canon_violations


def pending_checkpoint_reusable(
    revision, chapter, entry: dict, context_pack: dict, chapter_plan: dict
) -> bool:
    try:
        return _pending_checkpoint_reusable(
            revision,
            chapter,
            entry,
            context_pack,
            chapter_plan,
        )
    except Exception:
        # Persisted checkpoint data is untrusted here. Any malformed plan or
        # evidence must fail closed so the caller requires explicit regeneration.
        return False


def _pending_checkpoint_reusable(
    revision, chapter, entry: dict, context_pack: dict, chapter_plan: dict
) -> bool:
    plan = dict(revision.generation_plan or {})
    canon = validated_canon_checkpoint(plan)
    evidence = context_pack["evidence"]
    ledger = dict(revision.continuity_ledger or {})
    body = chapter.content_text if chapter else ""
    actual_chars = non_whitespace_chars(body)
    minimum, _target, maximum = chapter_length_range(chapter_plan)
    return bool(
        chapter
        and int(plan.get("version") or 0) >= 4
        and plan.get("status") == "ready"
        and plan.get("phase") == "ready"
        and canon
        and plan.get("plan_hash") == generation_plan_hash(plan)
        and entry.get("chapter_business_id") == chapter.business_id
        and chapter.content_hash == sha256_text(body)
        and entry.get("body_hash") == chapter.content_hash
        and entry.get("source_hash") == novel_chapter_source_hash(chapter)
        and entry.get("char_count") == actual_chars
        and minimum <= actual_chars <= maximum
        and entry.get("canon_hash") == evidence["canon_hash"] == canon["canon_hash"]
        and entry.get("context_hash") == evidence["context_hash"]
        and entry.get("state_before_hash") == evidence["state_before_hash"]
        and entry.get("context_evidence") == evidence
        and entry.get("state_pending_reason") == "source_evidence"
        and (entry.get("state_validation") or {}).get("status") == "failed"
        and entry.get("extraction_status") == "blocked"
        and ledger.get("state_status") == "failed"
        and int(ledger.get("recovery_from_position") or 0)
        == int(chapter_plan["position"])
        and _authoritative_state_is_empty(entry)
        and not _deterministic_body_violations(revision, chapter_plan, body)
    )


def _authoritative_state_is_empty(entry: dict) -> bool:
    return all(
        entry.get(key) is None
        for key in (
            "state_delta",
            "state_after",
            "state_after_hash",
            "plot_delta",
            "plot_delta_source",
            "plot_delta_version",
        )
    )


def _deterministic_body_violations(
    revision, chapter_plan: dict, body: str
) -> list[dict]:
    return [
        *required_event_anchor_violations(
            body,
            prompt_chapter_contract(chapter_plan),
        ),
        *premature_plan_violations(
            revision,
            int(chapter_plan["position"]),
            body,
        ),
        *revision_prose_canon_violations(revision, chapter_plan, body),
    ]
