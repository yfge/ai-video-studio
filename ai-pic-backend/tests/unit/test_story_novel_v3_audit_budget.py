import hashlib
import json
from types import SimpleNamespace

import anyio
import pytest
from app.services.story.story_novel_expected_delta import compile_expected_delta
from app.services.story.story_novel_sentence_spans import sentence_spans
from app.services.story.story_novel_state_service import initial_story_state
from app.services.story.story_novel_v3_audit_budget import (
    audit_contract_hash,
    reserve_audit_attempt,
)
from app.services.story.story_novel_v3_generation import audit_chapter
from app.services.story.story_novel_v3_repair import repair_failed_body
from tests.unit.test_story_novel_longform import _setup
from tests.unit.test_story_novel_v3_pipeline import _canon, _row


def test_audit_format_repair_does_not_exceed_remaining_budget():
    row = _row()
    canon = _canon()
    expected = compile_expected_delta(row, initial_story_state(canon))
    content = "第一日，长篇主角发现线索。"
    calls = []

    async def generate(_revision, _prompt, *, stage, **_kwargs):
        calls.append(stage)
        return "not-json"

    async def run():
        return await audit_chapter(
            SimpleNamespace(),
            1,
            content_text=content,
            sentence_index=sentence_spans(content),
            expected_delta=expected,
            canon=canon,
            chapter_plan=row,
            future_claim_cards=[],
            visible_world_rules=[],
            generate_text=generate,
            stage="audit.1.contract",
            max_calls=1,
        )

    with pytest.raises(ValueError, match="audit"):
        anyio.run(run)
    assert calls == ["audit.1.contract"]


def test_audit_receives_only_current_contract_semantics():
    row = _row()
    row["knowledge_grants"] = [
        {
            "character_id": "char-a",
            "fact_id": "fact-event-1-1",
            "source_event_id": "event-1",
        }
    ]
    canon = _canon()
    expected = compile_expected_delta(row, initial_story_state(canon))
    content = "第一日，长篇主角发现线索。"
    prompts = []

    async def generate(_revision, prompt, **_kwargs):
        prompts.append(prompt)
        return json.dumps(
            {
                "proofs": [{"contract_id": "event:event-1", "sentence_ids": ["S0001"]}],
                "unexpected_claims": [],
                "future_hits": [],
                "world_rule_hits": [],
            }
        )

    async def run():
        return await audit_chapter(
            SimpleNamespace(),
            1,
            content_text=content,
            sentence_index=sentence_spans(content),
            expected_delta=expected,
            canon=canon,
            chapter_plan=row,
            future_claim_cards=[],
            visible_world_rules=[],
            generate_text=generate,
            stage="audit.1.contract",
            max_calls=1,
            brief={
                "beats": [
                    {
                        "beat_id": "B01",
                        "purpose": "主角在当前事件中自然获知事实",
                        "bound_event_ids": ["event-1"],
                        "effect_contract_ids": ["event:event-1"],
                    }
                ]
            },
        )

    anyio.run(run)
    assert "主角在当前事件中自然获知事实" in prompts[0]
    assert '"character_names":["长篇主角"]' in prompts[0]
    assert '"source_key_event":"第一日，长篇主角发现线索"' in prompts[0]
    assert "未来章节秘密" not in prompts[0]


def test_local_repair_is_skipped_without_reaudit_budget():
    first = {
        "audit": {
            "passed": False,
            "failure_kind": "content",
            "repairable": True,
        },
        "audit_metrics": {"calls": 1, "attempts": [{}]},
    }

    async def forbidden(*_args, **_kwargs):
        raise AssertionError("provider must not be called")

    async def run():
        return await repair_failed_body(
            None,
            None,
            None,
            {"position": 1},
            {},
            {},
            {},
            {},
            first,
            forbidden,
            audit_stage="audit.1.contract",
            audit_call_budget=1,
            reserve_call=None,
            entry={},
        )

    selected, metrics, repair_count = anyio.run(run)
    assert selected is first
    assert metrics == {"audit": first["audit_metrics"]}
    assert repair_count == 0


def test_audit_reservations_are_durable_and_bounded(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session, with_character=True)
    entry = {"audit_budget_hash": "budget", "audit_contract_hash": "body"}
    revision.continuity_ledger = {"chapters": {"1": entry}}
    db_session.commit()

    for index in range(3):
        stage = reserve_audit_attempt(
            service,
            revision,
            entry,
            1,
            "budget",
            f"audit.1.budget.body.body.pass-{index}",
            task_id=task.id,
        )
        assert stage.endswith(entry["audit_reservations"][-1]["reservation_id"])
    with pytest.raises(ValueError, match="预算已耗尽"):
        reserve_audit_attempt(
            service,
            revision,
            entry,
            1,
            "budget",
            "audit.1.budget.body.body.fourth",
            task_id=task.id,
        )
    db_session.refresh(revision)
    stored = revision.continuity_ledger["chapters"]["1"]
    assert len(stored["audit_reservations"]) == 3


def test_local_reaudit_stage_binds_repaired_body_hash(monkeypatch):
    from app.services.story import story_novel_v3_repair as repair_module

    captured = {}
    repaired_prose = {"content_text": "修复后的正文", "block_contents": []}
    first = {
        "prose": {"block_contents": [{"block_id": "B01", "content_text": "旧正文"}]},
        "audit": {
            "passed": False,
            "failure_kind": "content",
            "repairable": True,
            "failed_block_ids": ["B01"],
            "repair_issues": [{"code": "future_hit"}],
            "state_validation": {"violations": [{"code": "future_hit"}]},
        },
        "audit_metrics": {"calls": 1, "attempts": [{"invocation_id": 1}]},
    }

    async def fake_repair(*_args, **_kwargs):
        return repaired_prose, {"calls": 1, "attempts": [{"invocation_id": 2}]}

    async def fake_evaluate(*_args, **kwargs):
        captured["stage"] = kwargs["audit_stage"]
        return {
            "prose": repaired_prose,
            "audit": {"passed": True},
            "audit_metrics": {"calls": 1, "attempts": [{"invocation_id": 3}]},
        }

    def fake_checkpoint(*args, **kwargs):
        captured["checkpoint"] = (args[8], kwargs["repair_resume"])
        return None, args[4]

    monkeypatch.setattr(repair_module, "update_progress", lambda *_args: None)
    monkeypatch.setattr(repair_module, "repair_blocks", fake_repair)
    monkeypatch.setattr(repair_module, "evaluate_body", fake_evaluate)
    monkeypatch.setattr(repair_module, "checkpoint_prose", fake_checkpoint)
    entry = {
        "chapter_contract_hash": "contract",
        "canon_hash": "canon",
        "context_hash": "context",
    }
    expected = {"delta_hash": "delta"}

    async def run():
        return await repair_failed_body(
            None,
            None,
            None,
            {"position": 1},
            {},
            {},
            {},
            expected,
            first,
            None,
            audit_stage="audit.1.budget",
            audit_call_budget=3,
            reserve_call=lambda stage: stage,
            entry=entry,
        )

    anyio.run(run)
    repaired_hash = audit_contract_hash(
        hashlib.sha256("修复后的正文".encode()).hexdigest(),
        expected,
        entry,
    )
    assert f".body.{repaired_hash}.local_repair" in captured["stage"]
    assert captured["checkpoint"][0] is repaired_prose
    assert captured["checkpoint"][1]["budget_hash"] is None
    assert captured["checkpoint"][1]["audit_metrics"] == first["audit_metrics"]
