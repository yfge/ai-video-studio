import pytest
from app.services.story.story_novel_v3_prompts import audit_contract_context
from app.services.story.story_novel_v3_proof_validation import merge_proof_audits
from tests.unit.test_story_novel_v3_audit_safety import _evaluate
from tests.unit.test_story_novel_v3_pipeline import _canon, _row


def test_source_bound_short_sentence_is_valid_event_proof():
    result, _prose = _evaluate(
        _row(),
        _canon(),
        [{"block_id": "B01", "content_text": "盐霜。"}],
        _payload([{"contract_id": "event:event-1", "sentence_ids": ["S0001"]}]),
    )

    assert result["passed"] is True


def test_source_bound_knowledge_reuses_source_event_sentence():
    row = _row()
    row["knowledge_grants"] = [
        {
            "character_id": "char-a",
            "fact_id": "fact-event-1-1",
            "source_event_id": "event-1",
        }
    ]
    result, _prose = _evaluate(
        row,
        _canon(),
        [
            {
                "block_id": "B01",
                "content_text": "长篇主角一字一字看过田契，终于明白南坡薄田已归自己承佃。",
            }
        ],
        _payload(
            [
                {"contract_id": "event:event-1", "sentence_ids": ["S0001"]},
                {"contract_id": "knowledge:1", "sentence_ids": ["S0001"]},
            ]
        ),
    )

    assert result["passed"] is True


def test_source_bound_knowledge_accepts_shared_semantic_sentence():
    row = _row()
    row["knowledge_grants"] = [
        {
            "character_id": "char-a",
            "fact_id": "fact-event-1-1",
            "source_event_id": "event-1",
        }
    ]
    result, _prose = _evaluate(
        row,
        _canon(),
        [
            {
                "block_id": "B01",
                "content_text": "发现异样。她仔细查看。长篇主角终于明白田契有误。",
            }
        ],
        _payload(
            [
                {
                    "contract_id": "event:event-1",
                    "sentence_ids": ["S0001", "S0003"],
                },
                {"contract_id": "knowledge:1", "sentence_ids": ["S0003"]},
            ]
        ),
    )

    assert result["passed"] is True


def test_source_bound_knowledge_accepts_later_sentence_bound_by_auditor():
    row = _row()
    row["knowledge_grants"] = [
        {
            "character_id": "char-a",
            "fact_id": "fact-event-1-1",
            "source_event_id": "event-1",
        }
    ]
    content = "发现异样。" + "无关动作。" * 5 + "终于明白田契有误。"
    result, _prose = _evaluate(
        row,
        _canon(),
        [{"block_id": "B01", "content_text": content}],
        _payload(
            [
                {"contract_id": "event:event-1", "sentence_ids": ["S0001"]},
                {"contract_id": "knowledge:1", "sentence_ids": ["S0007"]},
            ]
        ),
    )

    assert result["passed"] is True


def test_semantic_audit_still_blocks_unrelated_preexisting_knowledge():
    row = _row()
    row["knowledge_grants"] = [
        {
            "character_id": "char-a",
            "fact_id": "fact-event-1-1",
            "source_event_id": "event-1",
        }
    ]
    audit = _payload(
        [
            {"contract_id": "event:event-1", "sentence_ids": ["S0002"]},
            {"contract_id": "knowledge:1", "sentence_ids": ["S0001"]},
        ]
    )
    audit["unexpected_claims"] = [
        {"message": "角色在来源事件前凭空知道线索", "sentence_ids": ["S0001"]}
    ]
    result, _prose = _evaluate(
        row,
        _canon(),
        [{"block_id": "B01", "content_text": "他早已知道线索。后来才查到线索。"}],
        audit,
    )

    assert result["passed"] is False


def test_evidence_retry_overlays_instead_of_discarding_first_proofs():
    first = {
        "proofs": [
            {"contract_id": "state:1", "sentence_ids": ["S0001"]},
            {"contract_id": "knowledge:1", "sentence_ids": ["S0002"]},
        ],
        "missing_proof_contracts": ["event:event-1", "location:1"],
        **_issues(),
    }
    retry = {
        "proofs": [
            {"contract_id": "event:event-1", "sentence_ids": ["S0003"]},
            {"contract_id": "location:1", "sentence_ids": ["S0004"]},
        ],
        "missing_proof_contracts": ["state:1", "knowledge:1"],
        **_issues(),
    }

    merged = merge_proof_audits(first, retry)

    assert {item["contract_id"] for item in merged["proofs"]} == {
        "event:event-1",
        "state:1",
        "location:1",
        "knowledge:1",
    }
    assert merged["missing_proof_contracts"] == []


def test_timeline_audit_does_not_create_a_literal_date_proof_contract():
    row = _row()
    row["timeline_event_bindings"] = {"time-1": "event-1"}
    canon = _canon()
    canon["timeline"] = [
        {
            "id": "time-1",
            "story_time": "永和十二年正月十六",
            "label": "田契交割",
            "source_chapter_position": 1,
            "source_key_event": "永和十二年正月十六，田契交割",
        }
    ]
    result, _prose = _evaluate(
        row,
        canon,
        [{"block_id": "B01", "content_text": "正月十六，长篇主角收下田契。"}],
        _payload(
            [
                {"contract_id": "event:event-1", "sentence_ids": ["S0001"]},
            ]
        ),
    )

    assert result["passed"] is True


def test_later_chapter_timeline_accepts_relative_time_with_event_proof():
    row = _row()
    row["position"] = 2
    row["timeline_event_bindings"] = {"time-2": "event-1"}
    canon = _canon()
    canon["timeline"] = [
        {
            "id": "time-2",
            "story_time": "永和十二年正月十七",
            "label": "次日查看苗床",
            "source_chapter_position": 2,
            "source_key_event": "永和十二年正月十七，查看苗床",
        }
    ]
    result, _prose = _evaluate(
        row,
        canon,
        [{"block_id": "B01", "content_text": "次日清晨，长篇主角查看苗床。"}],
        _payload(
            [
                {"contract_id": "event:event-1", "sentence_ids": ["S0001"]},
            ]
        ),
    )

    assert result["passed"] is True


def test_audit_context_rejects_event_text_alignment_drift():
    row = _row()
    row["required_event_ids"] = ["event-1", "event-2"]

    with pytest.raises(ValueError, match="一一对应"):
        audit_contract_context(row, {"beats": []}, {}, _canon())


def test_audit_context_exposes_verified_background_without_changing_events():
    row = _row()

    context = audit_contract_context(
        row,
        {"beats": []},
        {},
        _canon(),
        established_background=["前章已确认水契由刘岩保管"],
    )

    assert context["established_background"] == ["前章已确认水契由刘岩保管"]
    assert context["current_events"] == [
        {"event_id": "event-1", "key_event": "第一日，长篇主角发现线索"}
    ]
    assert context["current_timeline"] == []


def _payload(proofs):
    return {"proofs": proofs, **_issues()}


def _issues():
    return {"unexpected_claims": [], "future_hits": [], "world_rule_hits": []}
