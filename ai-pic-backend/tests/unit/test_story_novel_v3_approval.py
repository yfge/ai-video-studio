import copy
import hashlib
import json

import anyio
import pytest
from app.models.llm_invocation import LLMInvocation
from app.models.narrative_memory import CharacterMemorySnapshot
from app.services.story.story_novel_chapter_brief_contract import (
    compile_chapter_brief_input,
)
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_context_utils import value_hash
from app.services.story.story_novel_future_guard_index import compile_future_guard_index
from app.services.story.story_novel_length_service import generation_plan_hash
from app.services.story.story_novel_planning_invocations import (
    valid as valid_planning_invocations,
)
from app.services.story.story_novel_prompt_renderer import (
    prompt_template_evidence as rendered_prompt_template_evidence,
)
from app.services.story.story_novel_prompt_renderer import v3_prompt_template_policy
from app.services.story.story_novel_state_service import initial_story_state
from app.services.story.story_novel_v3_approval import require_v3_quality
from app.services.story.story_novel_v3_context import build_v3_prose_input
from fastapi import HTTPException
from tests.unit.story_novel_v3_test_support import (
    freeze_planning_invocations,
    persisted_stage_text,
    prompt_template_evidence,
)
from tests.unit.test_story_novel_longform import _setup
from tests.unit.test_story_novel_v3_pipeline import _blocks, _brief, _canon, _row


def _evidence(stage: str, invocation_id: int) -> dict:
    model = (
        "planning"
        if stage.startswith("chapter_planning")
        else "prose" if stage.startswith("prose") else "audit"
    )
    return {
        "invocation_id": invocation_id,
        "provider": "deepseek",
        "model": model,
        "status": "succeeded",
        "input_tokens": 100,
        "output_tokens": 200,
        "finish_reason": "stop",
        "latency_ms": 10,
        "response_hash": hashlib.sha256(stage.encode()).hexdigest(),
        "raw_response_hash": hashlib.sha256(stage.encode()).hexdigest(),
    }


def _review_evidence(invocation_id: int) -> dict:
    return {
        **_evidence("audit.review", invocation_id),
        "model": "audit",
        "prompt_template": prompt_template_evidence("story_novel_continuity_review_v3"),
    }


def _invocation(invocation_id, revision, scene, model, response):
    return LLMInvocation(
        id=invocation_id,
        invocation_type="text",
        call_scene=f"story_novel.{revision.business_id}.{scene}",
        provider="deepseek",
        model=model,
        attempt_index=1,
        status="succeeded",
        original_prompt="prompt",
        prompt="prompt",
        response=response,
        input_tokens=100,
        cache_tokens=0,
        output_tokens=200,
        latency_ms=10,
        response_metadata={
            "finish_reason": "stop",
            "product_status": "accepted",
            "prompt_template": prompt_template_evidence(
                "story_novel_continuity_review_v3"
            ),
        },
        input_references=[
            {
                "type": "prompt_template",
                "value": prompt_template_evidence("story_novel_continuity_review_v3"),
            }
        ],
    )


def _ready_v3(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session, with_character=True)
    row = _row()
    canon = _canon()
    future = compile_future_guard_index([row], canon["milestones"], canon["entities"])
    plan = {
        "schema": "story_novel_generation_plan.v3",
        "version": 4,
        "status": "ready",
        "phase": "ready",
        "outline_hash": "outline-v3",
        "model_policy": {
            "planning_model": "deepseek:planning",
            "prose_model": "deepseek:prose",
            "audit_model": "deepseek:audit",
        },
        "planning_contract_version": 3,
        "event_execution_contract_version": 1,
        "state_compiler_version": 1,
        "future_guard_index": future,
        "future_guard_hash": future["index_hash"],
        "prompt_templates": v3_prompt_template_policy(),
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": 2,
        "chapter_count": 1,
        "chapters": [row],
    }
    revision.generation_plan = plan
    freeze_planning_invocations(revision, canon, [row], db=db_session)
    plan = dict(revision.generation_plan or {})
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    assert valid_planning_invocations(revision.generation_plan)
    revision.continuity_ledger = {
        "schema": "story_novel_continuity.v4",
        "state_status": "empty",
        "chapters": {},
    }
    revision.chapter_count = 1
    db_session.commit()
    invocation_id = 100

    async def generate(_revision, prompt, *, stage, **_kwargs):
        nonlocal invocation_id
        invocation_id += 1
        if stage.startswith("chapter_planning"):
            source = compile_chapter_brief_input(
                row,
                initial_story_state(canon),
                allowed_entity_ids=["char-a", "loc-gate"],
            )
            payload = _brief(source)
        elif stage.startswith("prose"):
            payload = {"blocks": _blocks(8)}
        else:
            payload = {
                "proofs": [{"contract_id": "event:event-1", "sentence_ids": ["S0001"]}],
                "unexpected_claims": [],
                "future_hits": [],
                "world_rule_hits": [],
            }
        text = json.dumps(payload, ensure_ascii=False)
        return persisted_stage_text(
            db_session,
            revision,
            stage,
            text,
            invocation_id,
            rendered_template=rendered_prompt_template_evidence(prompt),
            prompt_text=str(prompt),
        )

    anyio.run(generate_or_resume_chapter, service, revision, task, row, generate)
    assert valid_planning_invocations(revision.generation_plan)
    revision.continuity_report = {
        "review_invocations": [_review_evidence(201), _review_evidence(202)]
    }
    db_session.add_all(
        [
            _invocation(201, revision, "continuity.window.1", "audit", "audit.review"),
            _invocation(202, revision, "continuity.global", "audit", "audit.review"),
        ]
    )
    db_session.commit()
    return revision, revision.chapters, revision.continuity_ledger["chapters"]


def test_v3_quality_accepts_complete_hash_and_invocation_chain(db_session):
    revision, chapters, ledger = _ready_v3(db_session)
    before = db_session.query(CharacterMemorySnapshot).count()
    require_v3_quality(db_session, revision, chapters, ledger)
    assert db_session.query(CharacterMemorySnapshot).count() == before


def _exceed_audit_budget(entry):
    metric = entry["stage_metrics"]["audit"]
    metric["attempts"] = metric["attempts"] * 4
    metric["calls"] = 4
    metric["invocation_ids"] = [item["invocation_id"] for item in metric["attempts"]]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda entry: entry.update(brief_input_hash="stale"),
        lambda entry: entry["blocks"][0].update(content_hash="stale"),
        lambda entry: entry.update(sentence_index_hash="stale"),
        lambda entry: entry["future_audit"]["future_hits"].append(
            {"message": "提前兑现"}
        ),
        lambda entry: entry["stage_metrics"]["audit"]["attempts"][0].update(
            model="wrong"
        ),
        lambda entry: entry["stage_metrics"]["audit"]["attempts"][0].pop(
            "raw_response_hash"
        ),
        _exceed_audit_budget,
    ],
)
def test_v3_quality_rejects_tampered_chapter_chain(db_session, mutation):
    revision, chapters, ledger = _ready_v3(db_session)
    tampered = copy.deepcopy(ledger)
    mutation(tampered["1"])
    with pytest.raises(HTTPException, match="v3 质量/hash/调用证据"):
        require_v3_quality(db_session, revision, chapters, tampered)


def test_v3_quality_rebuilds_context_instead_of_trusting_self_reported_hashes(
    db_session,
):
    revision, chapters, ledger = _ready_v3(db_session)
    tampered = copy.deepcopy(ledger)
    entry = tampered["1"]
    entity = entry["brief_input"]["hard_constraints"]["compiled_canon"]["entities"][0]
    entity["name"] = "伪造角色"
    entry["brief_input_hash"] = value_hash(entry["brief_input"])
    entry["context_hash"] = entry["brief_input_hash"]
    entry["prose_context_hash"] = value_hash(
        build_v3_prose_input(
            {
                "brief_input": entry["brief_input"],
                "hard_constraints": entry["brief_input"]["hard_constraints"],
            },
            entry["chapter_brief"],
            revision.generation_plan["chapters"][0],
        )
    )

    with pytest.raises(HTTPException, match="v3 质量/hash/调用证据"):
        require_v3_quality(db_session, revision, chapters, tampered)


def test_v3_quality_requires_all_window_and_global_review_invocations(db_session):
    revision, chapters, ledger = _ready_v3(db_session)
    revision.continuity_report["review_invocations"] = [_review_evidence(201)]
    with pytest.raises(HTTPException, match="连续性审读调用证据不完整"):
        require_v3_quality(db_session, revision, chapters, ledger)
