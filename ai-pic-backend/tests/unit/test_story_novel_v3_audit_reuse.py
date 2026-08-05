from types import SimpleNamespace

import anyio
from app.models.llm_invocation import LLMInvocation
from app.services.story import story_novel_v3_audit_pipeline as pipeline
from app.services.story.story_novel_v3_audit_pipeline import reusable_audit_text
from app.services.story.story_novel_v3_proof_validation import (
    normalize_source_bound_proofs,
)
from tests.unit.story_novel_v3_test_support import persisted_stage_text
from tests.unit.test_story_novel_longform import _setup


def test_reusable_audit_requires_accepted_complete_response(db_session):
    _user, _story, _service, revision, _task, *_ = _setup(
        db_session, with_character=True
    )
    stage = "audit.1.budget.body.body.r01"
    persisted_stage_text(db_session, revision, stage, '{"proofs":[]}', 720)

    replay = reusable_audit_text(
        db_session, revision.business_id, "audit.1.budget.body.body"
    )

    assert str(replay) == '{"proofs":[]}'
    assert replay.invocation_evidence["invocation_id"] == 720

    row = db_session.get(LLMInvocation, 720)
    row.response_metadata = {
        **row.response_metadata,
        "product_status": "rejected",
    }
    db_session.commit()
    assert (
        reusable_audit_text(
            db_session, revision.business_id, "audit.1.budget.body.body"
        )
        is None
    )


def test_replayed_audit_preserves_budget_for_reaudit(monkeypatch):
    replay = SimpleNamespace(invocation_evidence={"invocation_id": 721})
    entry = {
        "body_hash": "body",
        "audit_contract_hash": "body",
        "audit_budget_hash": "budget",
    }
    captured = {}

    monkeypatch.setattr(pipeline, "prune_abandoned_reservations", lambda *_args: None)
    monkeypatch.setattr(pipeline, "persisted_audit_attempts", lambda *_args: 2)
    monkeypatch.setattr(pipeline, "audit_budget_available", lambda *_args: 1)
    monkeypatch.setattr(pipeline, "audit_contract_hash", lambda *_args: "body")
    monkeypatch.setattr(pipeline, "audit_stage", lambda *_args: "audit.1.budget")
    monkeypatch.setattr(pipeline, "reusable_audit_text", lambda *_args: replay)

    async def evaluate(*_args, **kwargs):
        captured["first_budget"] = kwargs["audit_call_budget"]
        captured["first_reserve"] = kwargs["reserve_call"]
        return {"audit": {}, "audit_metrics": {"calls": 1}}

    async def repair(*_args, **kwargs):
        captured["repair_budget"] = kwargs["audit_call_budget"]
        return "selected", {}, 1

    monkeypatch.setattr(pipeline, "evaluate_body", evaluate)
    monkeypatch.setattr(pipeline, "repair_failed_body", repair)

    async def run():
        return await pipeline.evaluate_and_repair(
            SimpleNamespace(db=object()),
            SimpleNamespace(business_id="revision"),
            SimpleNamespace(id=1),
            {"position": 1},
            {},
            {},
            {},
            {},
            {},
            None,
            entry=entry,
        )

    result = anyio.run(run)

    assert result == ("selected", {}, 1)
    assert captured == {
        "first_budget": 1,
        "first_reserve": None,
        "repair_budget": 2,
    }


def test_normalize_knowledge_proof_preserves_semantic_event_process_refs():
    spans = {
        sentence_id: {"sentence_id": sentence_id, "text": text}
        for sentence_id, text in (
            ("S0050", "顾砚提出早期疑问。"),
            ("S0083", "实测确认水轮只能供三亩。"),
            ("S0084", "顾砚据此确认上限。"),
        )
    }
    rows = [
        {
            "contract_id": "event:event-28-2",
            "sentence_ids": ["S0083", "S0084"],
            "spans": [spans["S0083"], spans["S0084"]],
            "quote": "实测确认水轮只能供三亩。……顾砚据此确认上限。",
        },
        {
            "contract_id": "knowledge:1",
            "sentence_ids": ["S0083", "S0084", "S0050"],
            "spans": [spans["S0083"], spans["S0084"], spans["S0050"]],
            "quote": "旧值",
        },
    ]

    normalized = normalize_source_bound_proofs(
        rows,
        {"knowledge_grants": [{"source_event_id": "event-28-2"}]},
    )

    knowledge = next(
        item for item in normalized if item["contract_id"] == "knowledge:1"
    )
    assert knowledge["sentence_ids"] == ["S0083", "S0084", "S0050"]
    assert knowledge["spans"] == [spans["S0083"], spans["S0084"], spans["S0050"]]
    assert knowledge["quote"] == "旧值"


def test_exhausted_evidence_budget_replays_latest_persisted_audit(monkeypatch):
    replay = SimpleNamespace(invocation_evidence={"invocation_id": 2325})
    entry = {
        "body_hash": "body",
        "audit_contract_hash": "body",
        "audit_budget_hash": "budget",
        "audit_failure_kind": "evidence_only",
    }
    captured = {}
    monkeypatch.setattr(pipeline, "prune_abandoned_reservations", lambda *_args: None)
    monkeypatch.setattr(pipeline, "persisted_audit_attempts", lambda *_args: 3)
    monkeypatch.setattr(pipeline, "audit_budget_available", lambda *_args: 0)
    monkeypatch.setattr(pipeline, "audit_contract_hash", lambda *_args: "body")
    monkeypatch.setattr(pipeline, "audit_stage", lambda *_args: "audit.28.budget")
    monkeypatch.setattr(pipeline, "reusable_audit_text", lambda *_args: replay)

    async def evaluate(*_args, **kwargs):
        captured.update(
            budget=kwargs["audit_call_budget"], reserve=kwargs["reserve_call"]
        )
        return {"audit": {"passed": True}, "audit_metrics": {"calls": 1}}

    async def repair(*_args, **_kwargs):
        return "selected", {}, 0

    monkeypatch.setattr(pipeline, "evaluate_body", evaluate)
    monkeypatch.setattr(pipeline, "repair_failed_body", repair)

    async def run():
        return await pipeline.evaluate_and_repair(
            SimpleNamespace(db=object()),
            SimpleNamespace(business_id="revision"),
            SimpleNamespace(id=6807),
            {"position": 28},
            {},
            {},
            {},
            {},
            {},
            None,
            entry=entry,
        )

    assert anyio.run(run) == ("selected", {}, 0)
    assert captured == {"budget": 1, "reserve": None}
