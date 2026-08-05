import json
from types import SimpleNamespace

import anyio
from app.services.story import story_novel_chapter_v3 as pipeline
from app.services.story import story_novel_v3_audit_pipeline as audit_pipeline
from app.services.story import story_novel_v3_repair as repair_flow
from app.services.story.story_novel_v3_gate import select_failed_result
from app.services.story.story_novel_v3_prompts import local_block_contract_retry_prompt


def test_audit_keeps_single_repair_for_combined_length_and_content_issues(monkeypatch):
    revision = SimpleNamespace(
        business_id="revision-v3",
        chapters=[],
        continuity_ledger={},
        generation_plan={},
    )
    service = SimpleNamespace(db=object())
    entry = {
        "body_hash": "body",
        "audit_contract_hash": "audit",
        "body_repair_count": 0,
    }
    context = {"brief_input": {"expected_delta": {}}, "evidence": {}}
    first = {
        "audit": {
            "passed": False,
            "state_validation": {
                "violations": [
                    {"code": "canon_violation", "message": "章节长度不足"},
                    {"code": "unexplained_location", "message": "计划外移动"},
                ]
            },
        },
        "prose": {},
        "audit_metrics": {"calls": 1},
    }
    calls = []

    monkeypatch.setattr(pipeline, "build_v3_planning_context", lambda *_args: context)
    monkeypatch.setattr(pipeline, "build_v3_prose_input", lambda *_args: {})
    monkeypatch.setattr(audit_pipeline, "audit_contract_hash", lambda *_args: "audit")
    monkeypatch.setattr(
        audit_pipeline, "prune_abandoned_reservations", lambda *_args: None
    )
    monkeypatch.setattr(audit_pipeline, "persisted_audit_attempts", lambda *_args: 0)
    monkeypatch.setattr(audit_pipeline, "audit_budget_available", lambda *_args: 2)
    monkeypatch.setattr(audit_pipeline, "audit_stage", lambda *_args: "audit.7")
    monkeypatch.setattr(
        audit_pipeline, "reserve_audit_attempt", lambda *_args, **_kw: "r"
    )
    monkeypatch.setattr(audit_pipeline, "reusable_audit_text", lambda *_args: None)

    async def brief_for(*_args):
        return {"beats": [], "brief_hash": "brief"}, entry

    async def prose_for(*_args):
        return {"content_text": "short", "block_contents": []}, entry

    async def evaluate(*_args, **_kwargs):
        calls.append("audit")
        return first

    async def repair(*_args, **kwargs):
        calls.append("repair")
        assert kwargs["allow_repair"] is True
        return {"audit": {"passed": True}}, {}, 1

    monkeypatch.setattr(pipeline, "_brief_for", brief_for)
    monkeypatch.setattr(pipeline, "_prose_for", prose_for)
    monkeypatch.setattr(audit_pipeline, "evaluate_body", evaluate)
    monkeypatch.setattr(audit_pipeline, "repair_failed_body", repair)
    monkeypatch.setattr(pipeline, "_finish", lambda *_args: "ready")

    result = anyio.run(
        pipeline.generate_or_resume_v3,
        service,
        revision,
        SimpleNamespace(id=7),
        {"position": 7},
        None,
    )

    assert result == "ready"
    assert calls == ["audit", "repair"]


def test_repair_selection_normalizes_dynamic_length_message():
    first = {
        "audit": {
            "passed": False,
            "state_validation": {
                "violations": [
                    {
                        "code": "canon_violation",
                        "reason_code": "length_out_of_range",
                        "message": "章节长度为 1974，要求 2000–3000",
                    },
                    {"code": "illegal_knowledge", "message": "家人提前获知"},
                ]
            },
        }
    }
    repaired = {
        "audit": {
            "passed": False,
            "state_validation": {
                "violations": [
                    {
                        "code": "canon_violation",
                        "reason_code": "length_out_of_range",
                        "message": "章节长度为 3069，要求 2000–3000",
                    }
                ]
            },
        }
    }

    assert select_failed_result(first, repaired) is repaired


def test_combined_repair_switches_to_pure_compression_on_length_retry():
    previous = {"replacements": [{"block_id": "B01", "content_text": "长" * 100}]}
    prompt = local_block_contract_retry_prompt(
        {
            "failed_block_ids": ["B01"],
            "failed_blocks": [{"block_id": "B01", "content_text": "旧正文"}],
            "chapter_brief": {"beats": [{"beat_id": "B01"}]},
            "current_chapter_context": {"events": [{"event": "加入当前合同材料"}]},
            "visible_canon": {"compiled_canon": {"world_rules": []}},
            "neighbor_blocks": [{"block_id": "B00", "content_text": "前文"}],
            "writing_style": {"genre": "drama"},
            "violations": [
                {
                    "code": "unexpected_claim",
                    "message": "未来剧情不得发送给正文模型",
                    "sentence_ids": ["S0004"],
                }
            ],
            "replacement_length": {"replacement_target_chars": 80},
        },
        json.dumps(previous, ensure_ascii=False),
        "local repair 合并正文长度为 100；请严格遵守 replacement_length",
    )

    assert "compress_previous_replacements" in prompt
    assert "previous_replacements_to_compress" in prompt
    assert '"chapter_brief"' not in prompt
    assert "旧正文" not in prompt
    assert "长" * 50 in prompt
    assert "加入当前合同材料" in prompt
    assert "未来剧情不得发送给正文模型" not in prompt
    assert "S0004" in prompt
    assert "前文" in prompt
    assert '"genre":"drama"' in prompt


def test_repair_cannot_swap_length_failure_for_new_evidence_failure():
    first = {
        "audit": {
            "passed": False,
            "failure_kind": "content",
            "state_validation": {
                "violations": [
                    {
                        "code": "canon_violation",
                        "reason_code": "length_out_of_range",
                    }
                ]
            },
        }
    }
    repaired = {
        "audit": {
            "passed": False,
            "failure_kind": "evidence_only",
            "state_validation": {
                "violations": [
                    {
                        "code": "canon_violation",
                        "reason_code": "knowledge_event_unbound",
                    }
                ]
            },
        }
    }

    assert select_failed_result(first, repaired) is first


def test_repaired_body_can_spend_remaining_budget_on_evidence_retry(monkeypatch):
    first = {
        "audit": {
            "passed": False,
            "failure_kind": "content",
            "repairable": True,
            "failed_block_ids": ["B01"],
            "repair_issues": [{"code": "length_out_of_range"}],
        },
        "prose": {"block_contents": [{"block_id": "B01", "content_text": "旧正文"}]},
        "audit_metrics": {"calls": 1, "attempts": []},
    }
    seen = {}
    entry = {"body_hash": "safe-first-body", "audit_contract_hash": "first"}

    async def repair_blocks(*_args, **_kwargs):
        return {
            "content_text": "新正文",
            "block_contents": [{"block_id": "B01", "content_text": "新正文"}],
        }, {"attempts": []}

    async def evaluate_body(*_args, **kwargs):
        seen.update(kwargs)
        return {
            "prose": {"content_text": "新正文"},
            "audit": {"passed": True},
            "audit_metrics": {"calls": 2, "attempts": []},
        }

    monkeypatch.setattr(repair_flow, "update_progress", lambda *_args: None)
    monkeypatch.setattr(repair_flow, "repair_blocks", repair_blocks)
    monkeypatch.setattr(repair_flow, "evaluate_body", evaluate_body)

    async def run():
        return await repair_flow.repair_failed_body(
            SimpleNamespace(),
            SimpleNamespace(),
            SimpleNamespace(),
            {"position": 11},
            {},
            {},
            {"chapter_length": {}},
            {},
            first,
            None,
            audit_stage="audit.11",
            audit_call_budget=3,
            reserve_call=None,
            entry=entry,
        )

    selected, _metrics, repair_count = anyio.run(run)

    assert selected["audit"]["passed"] is True
    assert seen["allow_evidence_retry"] is True
    assert seen["audit_call_budget"] == 2
    assert entry == {"body_hash": "safe-first-body", "audit_contract_hash": "first"}
    assert repair_count == 1
