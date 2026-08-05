import copy
from types import SimpleNamespace

from app.models.llm_invocation import LLMInvocation
from app.repositories.llm_invocation_repository import LLMInvocationRepository
from app.services.story.story_novel_invocation_evidence import invocation_row_evidence
from app.services.story.story_novel_v5_invocation_gate import (
    _valid_attempts,
    _valid_product_status,
)


def test_v5_invocation_gate_replays_persisted_response_and_prompt_hashes(db_session):
    template = _template("story_novel_prose_v5")
    row = LLMInvocation(
        id=9101,
        invocation_type="text",
        call_scene="story_novel.revision-v5.prose.1",
        provider="deepseek",
        model="prose",
        attempt_index=1,
        status="succeeded",
        original_prompt="prompt",
        prompt="prompt",
        response="正文。",
        input_references=[{"type": "prompt_template", "value": template}],
        response_metadata={"finish_reason": "stop", "product_status": "accepted"},
    )
    db_session.add(row)
    db_session.commit()
    attempt = invocation_row_evidence(row)
    revision = SimpleNamespace(business_id="revision-v5")
    plan = {"model_policy": {"prose_model": "deepseek:prose"}}

    assert _valid_attempts(
        LLMInvocationRepository(db_session), revision, [attempt], "prose", plan
    )
    tampered = copy.deepcopy(attempt)
    tampered["response_hash"] = "tampered"
    assert not _valid_attempts(
        LLMInvocationRepository(db_session), revision, [tampered], "prose", plan
    )


def test_v5_invocation_gate_allows_one_recoverable_truncation_only():
    truncated = {
        "product_status": "rejected",
        "finish_reason": "length",
    }
    continuation = {
        "product_status": "accepted",
        "prompt_template": _template("story_novel_prose_continuation_v5"),
    }

    assert _valid_product_status(truncated, [truncated, continuation], 0, "prose")
    assert not _valid_product_status(
        {**truncated, "finish_reason": "content_filter"},
        [truncated, continuation],
        0,
        "prose",
    )
    assert not _valid_product_status(truncated, [truncated], 0, "prose")


def _template(name):
    return {
        "template": name,
        "version": "1.0",
        "sources_hash": "source-hash",
        "rendered_hash": "rendered-hash",
        "system_prompt": {
            "template": "story_novel_system_v5",
            "version": "1.0",
            "sources_hash": "system-source-hash",
            "rendered_hash": "system-rendered-hash",
        },
    }
