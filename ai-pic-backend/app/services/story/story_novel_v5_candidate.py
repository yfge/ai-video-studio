"""Evaluate and annotate one persisted v5 prose candidate."""

from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_chapter_gate import chapter_length_range, non_whitespace_chars
from .story_novel_domain import sha256_text
from .story_novel_v5_generation import audit_candidate


async def evaluate_candidate(
    revision, position, chapter, contract, content, generate_text, index, kind, metrics
):
    result = await audit_candidate(
        revision,
        position,
        content,
        contract,
        generate_text,
        source_artifact_id=chapter.business_id,
        source_hash=novel_chapter_source_hash(chapter),
    )
    minimum, _target, maximum = chapter_length_range(contract["chapter"])
    count = non_whitespace_chars(content)
    result.update(
        attempt_index=index,
        attempt_kind=kind,
        body_hash=sha256_text(content),
        length_report={
            "status": "passed" if minimum <= count <= maximum else "failed",
            "actual_chars": count,
            "min_chars": minimum,
            "max_chars": maximum,
        },
        metrics={**metrics, **result["metrics"]},
    )
    return result


def candidate_passed(candidate):
    return bool(
        candidate["consistency_report"]["status"] == "passed"
        and candidate["readability_report"]["status"] == "passed"
        and candidate["length_report"]["status"] == "passed"
    )
