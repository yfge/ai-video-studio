from types import SimpleNamespace

from app.services.story.story_novel_prose_integrity import prose_integrity_violations
from app.services.story.story_novel_v3_gate import (
    failed_blocks_for_prose,
    prose_violations,
)


def _blocks():
    return [
        {"block_id": "B01", "content_text": "沈禾翻开田契，逐项核对水渠。"},
        {"block_id": "B02", "content_text": "顾砚记下结果，约定明日再测。"},
    ]


def test_integrity_accepts_complete_distinct_prose():
    assert prose_integrity_violations(_blocks()) == []


def test_integrity_locates_duplicate_passage_on_later_block():
    paragraph = "沈禾沿着田埂逐尺检查水痕，确认每条支沟都已通畅。" * 8
    violations = prose_integrity_violations(
        [
            {"block_id": "B01", "content_text": paragraph},
            {"block_id": "B02", "content_text": paragraph},
        ]
    )

    assert violations[0]["reason_code"] == "duplicate_passage"
    assert violations[0]["block_ids"] == ["B02"]
    assert violations[0]["source_block_id"] == "B01"


def test_integrity_rejects_literal_escape_quote_and_truncated_block():
    violations = prose_integrity_violations(
        [
            {"block_id": "B01", "content_text": "沈禾说：“先开沟。"},
            {"block_id": "B02", "content_text": r"顾砚答应。\n随后走向田埂"},
        ]
    )
    reasons = {item["reason_code"] for item in violations}

    assert reasons == {
        "literal_escape_sequence",
        "truncated_block_ending",
        "unbalanced_quote",
    }


def test_gate_maps_integrity_failure_directly_to_failed_block():
    blocks = _blocks()
    blocks[1]["content_text"] = "顾砚记下结果"
    prose = {
        "block_contents": blocks,
        "content_text": "\n\n".join(item["content_text"] for item in blocks),
        "char_count": 25,
    }
    plan = {"min_chars": 10, "target_chars": 20, "max_chars": 100}

    violations = prose_violations(SimpleNamespace(), plan, prose)

    assert [item["reason_code"] for item in violations] == ["truncated_block_ending"]
    assert failed_blocks_for_prose(violations, blocks, {"beats": []}) == ["B02"]
