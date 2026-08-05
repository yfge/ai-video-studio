import json
from types import SimpleNamespace

import anyio
from app.services.story.story_novel_block_contract import assemble_prose_blocks
from app.services.story.story_novel_expected_delta import compile_expected_delta
from app.services.story.story_novel_state_service import initial_story_state
from app.services.story.story_novel_v3_audit import (
    audit_contracts,
    evaluate_proof_audit,
    parse_proof_audit,
)
from app.services.story.story_novel_v3_generation import repair_blocks
from app.services.story.story_novel_v3_repair_guidance import repair_issues
from tests.unit.test_story_novel_v3_pipeline import _canon, _row


def _evaluate(row, canon, blocks, payload):
    prose = assemble_prose_blocks(blocks)
    state_before = initial_story_state(canon)
    expected = compile_expected_delta(row, state_before)
    contracts = audit_contracts(expected, canon, row)
    audit = parse_proof_audit(json.dumps(payload), contracts, prose["content_text"])
    brief = {
        "beats": [
            {"beat_id": item["block_id"], "effect_contract_ids": []} for item in blocks
        ]
    }
    return (
        evaluate_proof_audit(
            audit=audit,
            expected_delta=expected,
            canon=canon,
            chapter_plan=row,
            state_before=state_before,
            content_text=prose["content_text"],
            brief=brief,
            block_manifest=prose["blocks"],
        ),
        prose,
    )


def test_knowledge_proof_can_follow_its_source_event_in_a_later_sentence():
    canon = _canon()
    row = _row()
    row["knowledge_grants"] = [
        {
            "character_id": "char-a",
            "fact_id": "fact-event-1-1",
            "source_event_id": "event-1",
        }
    ]
    blocks = [
        {"block_id": "B01", "content_text": "第一日，长篇主角发现线索。"},
        {"block_id": "B02", "content_text": "雨停了，城门外只剩水声。"},
    ]
    result, _prose = _evaluate(
        row,
        canon,
        blocks,
        {
            "proofs": [
                {"contract_id": "event:event-1", "sentence_ids": ["S0001"]},
                {"contract_id": "knowledge:1", "sentence_ids": ["S0002"]},
            ],
            "unexpected_claims": [],
            "future_hits": [],
            "world_rule_hits": [],
        },
    )

    assert result["passed"] is True


def test_knowledge_discovery_can_precede_completion_of_same_source_event():
    canon = _canon()
    row = _row()
    row["knowledge_grants"] = [
        {
            "character_id": "char-a",
            "fact_id": "fact-event-1-1",
            "source_event_id": "event-1",
        }
    ]
    blocks = [
        {"block_id": "B01", "content_text": "他比对旧砖，发现城门暗槽的线索。"},
        {"block_id": "B02", "content_text": "随后，他完成查验并记下暗槽位置。"},
    ]
    result, _prose = _evaluate(
        row,
        canon,
        blocks,
        {
            "proofs": [
                {"contract_id": "event:event-1", "sentence_ids": ["S0002"]},
                {"contract_id": "knowledge:1", "sentence_ids": ["S0001"]},
            ],
            "unexpected_claims": [],
            "future_hits": [],
            "world_rule_hits": [],
        },
    )

    assert result["passed"] is True


def test_future_audit_message_is_redacted_from_local_repair_prompt():
    secret = "第十九章才允许揭示的增旱阀仓真相"
    row = _row()
    blocks = [
        {"block_id": "B01", "content_text": "第一日，长篇主角发现线索。"},
        {"block_id": "B02", "content_text": "他忽然说出一项不该知道的结论。"},
    ]
    result, prose = _evaluate(
        row,
        _canon(),
        blocks,
        {
            "proofs": [{"contract_id": "event:event-1", "sentence_ids": ["S0001"]}],
            "unexpected_claims": [],
            "future_hits": [
                {
                    "message": secret,
                    "sentence_ids": ["S0002"],
                    "claim_id": "event:future-secret",
                }
            ],
            "world_rule_hits": [],
        },
    )
    captured = []

    async def generate(_revision, prompt, **_kwargs):
        captured.append(prompt)
        return json.dumps(
            {"replacements": [{"block_id": "B02", "content_text": "他及时收住话头。"}]},
            ensure_ascii=False,
        )

    async def run_repair():
        return await repair_blocks(
            SimpleNamespace(),
            1,
            blocks=blocks,
            failed_block_ids=result["failed_block_ids"],
            violations=result["repair_issues"],
            prose_input={
                "chapter_brief": {"beats": []},
                "visible_canon": {},
                "chapter_length": {"min_chars": 1, "target_chars": 10, "max_chars": 50},
            },
            generate_text=generate,
        )

    repaired, _metrics = anyio.run(run_repair)

    assert prose["content_text"] != repaired["content_text"]
    assert result["failed_block_ids"] == ["B02"]
    assert secret not in captured[0]
    assert "future_hit" in captured[0]
    assert "event:future-secret" not in captured[0]
    assert "S0002" in captured[0]


def test_all_model_issue_messages_are_redacted_from_writer_guidance():
    rows = repair_issues(
        {
            "unexpected_claims": [
                {"message": "当前章东西方位矛盾", "sentence_ids": ["S0001"]}
            ],
            "future_hits": [{"message": "未来章节秘密", "sentence_ids": ["S0002"]}],
            "world_rule_hits": [
                {
                    "rule_id": "rule-labor",
                    "message": "当前章劳力耗时不现实",
                    "sentence_ids": ["S0003"],
                }
            ],
        }
    )

    assert all("message" not in item for item in rows)
    assert rows[0]["sentence_ids"] == ["S0001"]
    assert rows[1]["code"] == "future_hit"
    assert rows[2]["rule_id"] == "rule-labor"


def test_plan_state_inconsistency_is_not_sent_to_prose_repair():
    row = _row()
    row["preconditions"] = [
        {
            "subject_id": "char-a",
            "field": "status",
            "operator": "eq",
            "value": "ready",
        }
    ]
    result, _prose = _evaluate(
        row,
        _canon(),
        [{"block_id": "B01", "content_text": "第一日，长篇主角发现线索。"}],
        {
            "proofs": [{"contract_id": "event:event-1", "sentence_ids": ["S0001"]}],
            "unexpected_claims": [],
            "future_hits": [],
            "world_rule_hits": [],
        },
    )

    assert result["passed"] is False
    assert result["repairable"] is False
    assert result["state_contract_failed"] is True
    assert result["repair_issues"] == []
    assert any(
        item["code"] == "state_reversion"
        for item in result["state_validation"]["violations"]
    )


def test_deterministic_error_does_not_override_state_contract_failure():
    from app.services.story.story_novel_v3_evaluation import (
        _attach_deterministic_blocks,
    )

    evaluated = {
        "repairable": False,
        "state_contract_failed": True,
        "repair_issues": [],
        "failed_block_ids": [],
    }
    prose = {"block_contents": [{"block_id": "B01", "content_text": "短正文"}]}
    brief = {"beats": [{"beat_id": "B01"}]}
    _attach_deterministic_blocks(
        evaluated,
        [{"code": "length", "message": "正文过短"}],
        prose,
        brief,
    )

    assert evaluated["repairable"] is False
    assert evaluated["failed_block_ids"] == ["B01"]
