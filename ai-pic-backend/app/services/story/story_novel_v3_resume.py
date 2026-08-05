"""Hash-bound reuse decisions for v3 chapter checkpoints."""

from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_block_contract import parse_prose_blocks
from .story_novel_chapter_brief_contract import validate_chapter_brief
from .story_novel_sentence_spans import resolve_sentence_refs
from .story_novel_state_service import replay_checkpoint_state, state_hash


def reusable_brief(entry: dict, context: dict, chapter_plan: dict) -> dict | None:
    brief = entry.get("chapter_brief")
    if (
        entry.get("status") == "gate_failed"
        or not isinstance(brief, dict)
        or entry.get("brief_input_hash") != context["evidence"]["context_hash"]
        or entry.get("chapter_contract_hash")
        != context["evidence"]["chapter_contract_hash"]
        or entry.get("state_before_hash") != context["evidence"]["state_before_hash"]
    ):
        return None
    try:
        return validate_chapter_brief(brief, context["brief_input"])
    except (TypeError, ValueError):
        return None


def reusable_body(
    entry: dict, chapter, context: dict, brief: dict
) -> list[dict] | None:
    if (
        chapter is None
        or entry.get("status") not in {"audit", "memory_ready", "ready"}
        or entry.get("body_hash") != chapter.content_hash
        or entry.get("source_hash") != novel_chapter_source_hash(chapter)
        or entry.get("context_hash") != context["evidence"]["context_hash"]
        or entry.get("brief_hash") != brief["brief_hash"]
    ):
        return None
    try:
        blocks = [
            {
                "block_id": item["block_id"],
                "content_text": chapter.content_text[item["start"] : item["end"]],
            }
            for item in entry.get("blocks") or []
        ]
        return parse_prose_blocks(
            {"blocks": blocks}, expected_count=len(brief["beats"])
        )
    except (KeyError, TypeError, ValueError):
        return None


def reusable_verified_body(entry, chapter, context, brief) -> bool:
    if reusable_body(entry, chapter, context, brief) is None:
        return False
    if not proofs_match_body(entry, chapter):
        return False
    replayed = replay_checkpoint_state(context["state_before"], entry)
    return bool(
        entry.get("status") in {"memory_ready", "ready"}
        and (entry.get("state_validation") or {}).get("status") == "passed"
        and replayed is not None
        and entry.get("state_after_hash") == state_hash(replayed)
    )


def proofs_match_body(entry: dict, chapter) -> bool:
    try:
        for proof in entry.get("proof_spans") or []:
            resolved = resolve_sentence_refs(
                chapter.content_text,
                proof["sentence_ids"],
                expected_source_hash=proof["source_hash"],
            )
            stored = {
                key: proof[key]
                for key in (
                    "source_hash",
                    "sentence_index_hash",
                    "sentence_ids",
                    "spans",
                    "quote",
                )
            }
            if resolved != stored:
                return False
    except (KeyError, TypeError, ValueError):
        return False
    return True
