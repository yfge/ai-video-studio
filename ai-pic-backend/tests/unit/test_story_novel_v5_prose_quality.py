import pytest
import anyio

from app.services.story.story_novel_export_ai import TruncatedNovelOutput
from app.services.story.story_novel_invocation_evidence import GeneratedNovelText
from app.services.story.story_novel_sentence_spans import sentence_spans
from app.services.story.story_novel_v5_generation import generate_prose
from app.services.story.story_novel_v5_readability import (
    candidate_rank,
    repair_span,
    validate_readability,
)
from app.services.story.story_novel_v5_text import (
    complete_sentence_prefix,
    merge_continuation,
    replace_span,
)


def test_truncation_merges_only_at_complete_sentence_and_removes_overlap():
    partial = "第一句完整。第二句也完整。第三句没有写完"
    prefix = complete_sentence_prefix(partial)

    merged = merge_continuation(prefix, "第二句也完整。第三句终于写完。")

    assert prefix == "第一句完整。第二句也完整。"
    assert merged == "第一句完整。第二句也完整。第三句终于写完。"


def test_sentence_span_repair_changes_only_the_selected_contiguous_range():
    content = "第一句。第二句太重复。第三句收束。"

    replaced = replace_span(content, ["S0002"], "第二句变得自然。")

    assert replaced == "第一句。第二句变得自然。第三句收束。"
    assert sentence_spans(replaced)[0]["text"] == "第一句。"
    assert sentence_spans(replaced)[-1]["text"] == "第三句收束。"


def test_readability_requires_all_dimensions_and_evidence_bound_blockers():
    sentences = sentence_spans("第一句。第二句。")
    report = _report(score=8)
    report["issues"] = [
        {
            "id": "R1",
            "severity": "blocking",
            "dimension_id": "repetition",
            "sentence_ids": ["S0002"],
            "message": "重复",
        }
    ]

    validated = validate_readability(report, sentences)

    assert validated["status"] == "failed"
    assert repair_span(validated, sentences) == ["S0002"]
    report["issues"][0]["sentence_ids"] = []
    with pytest.raises(ValueError, match="lacks evidence"):
        validate_readability(report, sentences)


def test_best_candidate_order_prefers_hard_consistency_then_readability_then_age():
    candidates = [
        _candidate(0, "failed", 10, 0),
        _candidate(1, "passed", 7, 2),
        _candidate(2, "passed", 8, 1),
        _candidate(3, "passed", 8, 1),
    ]

    assert max(candidates, key=candidate_rank)["attempt_index"] == 2


def test_continuous_prose_allows_exactly_one_sentence_boundary_continuation():
    calls = []

    async def generate(_revision, _prompt, *, stage, **_kwargs):
        calls.append(stage)
        if len(calls) == 1:
            raise TruncatedNovelOutput(
                "length",
                "第一句完整。第二句没有写完",
                {"invocation_id": 1},
                finish_reason="length",
            )
        return GeneratedNovelText(
            "第一句完整。第二句终于完成。",
            {"invocation_id": 2},
        )

    content, metrics = anyio.run(
        generate_prose,
        object(),
        1,
        {
            "target_chars": 20,
            "max_chars": 30,
            "allowed_events": [],
            "obligations": [],
            "scene_plan": {"hook": "继续"},
        },
        generate,
    )

    assert calls == ["prose.1", "prose.1.truncation_continue"]
    assert content == "第一句完整。第二句终于完成。"
    assert metrics["calls"] == 2


def _report(score):
    ids = (
        "scene_transitions",
        "language_naturalness",
        "character_voice",
        "dialogue",
        "repetition",
        "exposition_density",
    )
    return {
        "dimensions": [
            {"id": item, "applies": True, "score": score, "reason": "ok"}
            for item in ids
        ],
        "issues": [],
        "summary": "ok",
    }


def _candidate(index, consistency, score, issue_count):
    return {
        "attempt_index": index,
        "consistency_report": {"status": consistency},
        "readability_report": {
            "score": score,
            "issues": [{} for _ in range(issue_count)],
        },
    }
