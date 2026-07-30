import json
from types import SimpleNamespace

import pytest
from app.services.story.story_novel_block_contract import assemble_prose_blocks
from app.services.story.story_novel_expected_delta import compile_expected_delta
from app.services.story.story_novel_v3_audit import (
    audit_contracts,
    evaluate_proof_audit,
    parse_proof_audit,
)
from app.services.story.story_novel_v3_context import (
    _add_rows,
    build_v3_planning_context,
    build_v3_prose_input,
)
from app.services.story.story_novel_v3_evaluation import _established_background
from tests.unit.test_story_novel_v3_pipeline import _canon, _row


def test_prose_input_excludes_raw_event_memory_expected_delta_and_future_context():
    context = {
        "brief_input": {
            "hard_constraints": {"story_invariants": {"genre": "drama"}},
            "planning_evidence": {
                "world_events": [{"business_id": "evt-secret"}],
                "character_memories": [{"business_id": "mem-secret"}],
            },
        },
        "hard_constraints": {
            "compiled_canon": {"entities": []},
            "approved_story_canon": {
                "approved_events": [{"summary": "raw-event-secret"}],
                "character_snapshots": [
                    {"memories": [{"content": "raw-memory-secret"}]}
                ],
            },
        },
    }
    result = build_v3_prose_input(context, {"beats": []}, _row())
    surface = json.dumps(result, ensure_ascii=False)
    for secret in (
        "evt-secret",
        "mem-secret",
        "raw-event-secret",
        "raw-memory-secret",
        "expected_delta",
    ):
        assert secret not in surface
    assert result["prompt_evidence"] == {
        "raw_world_event_count": 0,
        "raw_character_memory_count": 0,
        "future_chapter_count": 0,
    }


def test_audit_rejects_model_authored_state_and_binds_source_spans():
    row = _row()
    state = {
        "subjects": {"char-a": {"location": "loc-gate"}},
        "occurred_event_ids": [],
        "completed_milestone_ids": [],
        "threads": {},
    }
    expected = compile_expected_delta(row, state)
    body = "第一日，长篇主角发现线索。"
    contracts = audit_contracts(expected, _canon(), row)
    with pytest.raises(ValueError, match="audit 只能"):
        parse_proof_audit(
            json.dumps(
                {
                    "proofs": [],
                    "unexpected_claims": [],
                    "future_hits": [],
                    "world_rule_hits": [],
                    "state_delta": {"occurred_event_ids": []},
                }
            ),
            contracts,
            body,
        )
    audit = parse_proof_audit(
        json.dumps(
            {
                "proofs": [{"contract_id": "event:event-1", "sentence_ids": ["S0001"]}],
                "unexpected_claims": [],
                "future_hits": [],
                "world_rule_hits": [],
            }
        ),
        contracts,
        body,
    )
    block = assemble_prose_blocks([{"block_id": "B01", "content_text": body}])
    result = evaluate_proof_audit(
        audit=audit,
        expected_delta=expected,
        canon=_canon(),
        chapter_plan=row,
        state_before=state,
        content_text=body,
        brief={"beats": [{"beat_id": "B01", "effect_contract_ids": ["event:event-1"]}]},
        block_manifest=block["blocks"],
    )
    assert result["passed"] is True
    assert result["state_delta"]["occurred_event_ids"] == ["event-1"]
    assert result["proof_spans"][0]["quote"] == body


def test_context_budget_truncates_only_at_complete_planning_evidence_rows():
    pack = {"hard_constraints": {"canon_hash": "c"}}
    rows = [
        {"business_id": f"evt-{index}", "source_hash": "x" * 64, "summary": "字" * 4000}
        for index in range(20)
    ]
    truncations = []
    _add_rows(pack, "world_events", rows, truncations)

    assert isinstance(pack["world_events"], list)
    assert 0 < len(pack["world_events"]) < len(rows)
    assert all(isinstance(item, dict) for item in pack["world_events"])
    assert truncations == [
        {
            "section": "world_events",
            "original_items": len(rows),
            "kept_items": len(pack["world_events"]),
        }
    ]


def test_planning_context_keeps_recent_plot_before_large_memory_pool(monkeypatch):
    previous = SimpleNamespace(
        business_id="chapter-1",
        position=1,
        title="前章",
        summary="前章摘要",
        cliffhanger="前章卡点",
        content_hash="body-1",
        content_text="前章尾部" * 800,
    )
    evidence = [
        {
            "business_id": f"event-{index}",
            "source_hash": f"source-{index}",
            "summary": "历史证据" * 1000,
        }
        for index in range(30)
    ]
    monkeypatch.setattr(
        "app.services.story.story_novel_v3_context.ready_prior_chapters",
        lambda *_args, **_kwargs: [previous],
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_v3_context.state_before_position",
        lambda *_args, **_kwargs: {"subjects": {}, "threads": {}},
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_v3_context.chapter_memory_context",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_v3_context.revision_local_candidates",
        lambda *_args, **_kwargs: (evidence, evidence),
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_v3_context.build_hard_constraints",
        lambda **_kwargs: {"compiled_canon": {"entities": []}},
    )
    revision = SimpleNamespace(
        generation_plan={"canon": {}, "chapters": [_row()]},
        story_snapshot={},
        continuity_ledger={"chapters": {}},
    )

    context = build_v3_planning_context(
        SimpleNamespace(db=object()), revision, 2, {**_row(), "position": 2}
    )

    assert context["brief_input"]["recent_chapters"][0]["business_id"] == "chapter-1"
    assert context["brief_input"]["previous_chapter_tail"].endswith("前章尾部")


def test_audit_issue_sentence_ids_are_validated_and_source_bound():
    body = "第一句正常。第二句提前揭示未来结论。第三句收束。"
    contracts = []
    parsed = parse_proof_audit(
        json.dumps(
            {
                "proofs": [],
                "unexpected_claims": [],
                "future_hits": [
                    {
                        "claim_id": "event:future",
                        "message": "提前兑现",
                        "sentence_ids": ["S0002"],
                    }
                ],
                "world_rule_hits": [],
            },
            ensure_ascii=False,
        ),
        contracts,
        body,
    )
    assert parsed["future_hits"][0]["quote"] == "第二句提前揭示未来结论。"
    with pytest.raises(ValueError, match="issue 结构无效"):
        parse_proof_audit(
            json.dumps(
                {
                    "proofs": [],
                    "unexpected_claims": [],
                    "future_hits": ["提前兑现"],
                    "world_rule_hits": [],
                },
                ensure_ascii=False,
            ),
            contracts,
            body,
        )


def test_future_issue_must_use_future_bucket_and_claim_id():
    body = "当前章提前兑现未来权限。"
    base = {"proofs": [], "world_rule_hits": []}
    with pytest.raises(ValueError, match="future claim 必须归入 future_hits"):
        parse_proof_audit(
            json.dumps(
                {
                    **base,
                    "unexpected_claims": [
                        {
                            "claim_id": "state:8:1",
                            "message": "未来权限已生效",
                            "sentence_ids": ["S0001"],
                        }
                    ],
                    "future_hits": [],
                },
                ensure_ascii=False,
            ),
            [],
            body,
        )
    with pytest.raises(ValueError, match="future_hits 必须绑定 claim_id"):
        parse_proof_audit(
            json.dumps(
                {
                    **base,
                    "unexpected_claims": [],
                    "future_hits": [
                        {"message": "未来权限已生效", "sentence_ids": ["S0001"]}
                    ],
                },
                ensure_ascii=False,
            ),
            [],
            body,
        )


def test_audit_background_uses_only_prior_ready_verified_events():
    context = {
        "brief_input": {
            "prior_ledger": {
                "1": {
                    "status": "ready",
                    "body_hash": "body-1",
                    "source_hash": "source-1",
                    "plot_delta_source": "expected_delta",
                    "plot_delta_version": 2,
                    "state_validation": {"status": "passed"},
                    "plot_delta": {"key_events": ["前章已验证水契归属"]},
                },
                "2": {
                    "status": "gate_failed",
                    "plot_delta": {"key_events": ["失败正文不得进入"]},
                },
            },
            "chapter_contract": {"position": 3},
        }
    }

    assert _established_background(context) == [
        {
            "chapter_position": 1,
            "key_event": "前章已验证水契归属",
            "source_hash": "source-1",
        }
    ]
