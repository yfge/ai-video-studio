import json

from app.models.llm_invocation import LLMInvocation
from app.services.story.story_novel_invocation_evidence import invocation_row_evidence
from app.services.story.story_novel_prose_length_evidence import (
    reconstruct_initial_prose,
)


def test_reconstruction_binds_single_accepted_provider_response(db_session):
    evidence = _store(
        db_session,
        701,
        "story_novel.rev-length.prose.1",
        _blocks("甲" * 100, "乙" * 120),
    )

    result = reconstruct_initial_prose(
        db_session, "rev-length", 1, _metric(evidence), 2
    )

    assert result["observed_output_chars"] == 220
    assert result["source_invocation_ids"] == [701]
    assert len(result["initial_prose_body_hash"]) == 64


def test_format_repair_uses_only_the_response_that_produced_the_blocks(db_session):
    failed = _store(db_session, 702, "story_novel.rev-length.prose.2", '{"blocks":[')
    accepted = _store(
        db_session,
        703,
        "story_novel.rev-length.prose.2.format_repair",
        _blocks("丙" * 80),
    )

    result = reconstruct_initial_prose(
        db_session, "rev-length", 2, _metric(failed, accepted), 1
    )

    assert result["observed_output_chars"] == 80
    assert result["source_invocation_ids"] == [703]


def test_truncation_continuation_binds_both_contributing_responses(db_session):
    partial = _store(
        db_session,
        704,
        "story_novel.rev-length.prose.3",
        '{"blocks":[{"block_id":"B01","content_text":"甲甲"},'
        '{"block_id":"B02","content_text":"未完',
        finish_reason="length",
        product_status="rejected",
    )
    continuation = _store(
        db_session,
        705,
        "story_novel.rev-length.prose.3.truncation_continue",
        json.dumps(
            {"blocks": [{"block_id": "B02", "content_text": "乙乙乙"}]},
            ensure_ascii=False,
        ),
    )

    result = reconstruct_initial_prose(
        db_session, "rev-length", 3, _metric(partial, continuation), 2
    )

    assert result["observed_output_chars"] == 5
    assert result["source_invocation_ids"] == [704, 705]


def test_complete_blocks_recovered_from_a_truncated_envelope(db_session):
    evidence = _store(
        db_session,
        707,
        "story_novel.rev-length.prose.5",
        _blocks("戊" * 60, "己" * 70),
        finish_reason="length",
        product_status="rejected",
    )

    result = reconstruct_initial_prose(
        db_session, "rev-length", 5, _metric(evidence), 2
    )

    assert result["observed_output_chars"] == 130
    assert result["source_invocation_ids"] == [707]


def test_content_filtered_blocks_are_never_recovered(db_session):
    evidence = _store(
        db_session,
        708,
        "story_novel.rev-length.prose.6",
        _blocks("庚" * 60),
        finish_reason="content_filter",
        product_status="rejected",
    )

    assert (
        reconstruct_initial_prose(db_session, "rev-length", 6, _metric(evidence), 1)
        is None
    )


def test_tampered_product_response_hash_is_not_a_usable_observation(db_session):
    evidence = _store(
        db_session,
        706,
        "story_novel.rev-length.prose.4",
        _blocks("丁" * 50),
    )
    evidence["response_hash"] = "tampered"

    assert (
        reconstruct_initial_prose(db_session, "rev-length", 4, _metric(evidence), 1)
        is None
    )


def _blocks(*contents):
    return json.dumps(
        {
            "blocks": [
                {"block_id": f"B{index:02d}", "content_text": content}
                for index, content in enumerate(contents, 1)
            ]
        },
        ensure_ascii=False,
    )


def _metric(*attempts):
    return {
        "calls": len(attempts),
        "invocation_ids": [item["invocation_id"] for item in attempts],
        "attempts": list(attempts),
    }


def _store(
    db,
    invocation_id,
    scene,
    response,
    *,
    finish_reason="stop",
    product_status="accepted",
):
    row = LLMInvocation(
        id=invocation_id,
        invocation_type="text",
        call_scene=scene,
        provider="deepseek",
        model="deepseek-v4-flash",
        attempt_index=1,
        status="succeeded",
        original_prompt="prompt",
        prompt="prompt",
        response=response,
        input_tokens=10,
        cache_tokens=0,
        output_tokens=10,
        latency_ms=1,
        response_metadata={
            "finish_reason": finish_reason,
            "product_status": product_status,
        },
    )
    db.add(row)
    db.flush()
    return invocation_row_evidence(row)
