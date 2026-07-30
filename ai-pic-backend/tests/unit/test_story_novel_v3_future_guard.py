import json

import pytest
from app.services.story.story_novel_context_utils import value_hash
from app.services.story.story_novel_future_guard_index import (
    compile_future_guard_index,
    future_claim_cards,
    future_guard_index_matches,
)


def _chapters():
    return [
        {
            "position": 1,
            "goal": "第一章目标不应进入索引",
            "end_state": "第一章终态不应进入索引",
            "required_event_ids": ["event-sample"],
            "key_events": ["苏砚封存样本，来源仍未知"],
            "future_guard_entity_ids": ["char-su-yan", "sample-r17"],
            "milestones_consumed": [],
        },
        {
            "position": 19,
            "goal": "完整未来目标禁止进入正文",
            "end_state": "完整未来终态禁止进入正文",
            "required_event_ids": ["event-r17-confirmed"],
            "key_events": ["2174年9月21日，化验确认R-17来自人工增旱阀仓"],
            "future_guard_entity_ids": ["sample-r17"],
            "milestones_consumed": ["mile-r17-confirmed"],
        },
    ]


def test_future_guard_is_compact_and_omits_future_goal_and_end_state():
    index = compile_future_guard_index(
        _chapters(),
        milestones=[
            {
                "id": "mile-r17-confirmed",
                "outcomes": [
                    {"subject_id": "sample-r17", "field": "source", "value": "阀仓"}
                ],
            }
        ],
    )
    encoded = json.dumps(index, ensure_ascii=False)

    assert "完整未来目标禁止进入正文" not in encoded
    assert "完整未来终态禁止进入正文" not in encoded
    event = next(
        item
        for item in index["claims"]
        if item["claim_id"] == "event:event-r17-confirmed"
    )
    assert event["first_allowed_position"] == 19
    assert event["protected_dates"] == ["2174年9月21日"]
    assert event["claim_fingerprint"]
    assert index["index_hash"]


def test_future_guard_hash_ignores_runtime_chapter_fields():
    chapters = _chapters()
    before = compile_future_guard_index(chapters)
    chapters = json.loads(json.dumps(chapters, sort_keys=True))
    chapters[0].update(
        {
            "actual_chars": 2211,
            "generation_status": "audit",
            "context_hash": "context-hash",
            "body_hash": "body-hash",
            "source_hash": "source-hash",
            "extraction_status": "pending",
        }
    )

    assert compile_future_guard_index(chapters) == before


def test_future_guard_accepts_only_legacy_match_term_drift():
    expected = compile_future_guard_index(_chapters())
    legacy = json.loads(json.dumps(expected))
    legacy["claims"][1]["match_terms"] = ["旧顺序派生词"]
    claim = dict(legacy["claims"][1])
    claim.pop("claim_fingerprint")
    legacy["claims"][1]["claim_fingerprint"] = value_hash(claim)
    payload = dict(legacy)
    payload.pop("index_hash")
    legacy["index_hash"] = value_hash(payload)

    assert future_guard_index_matches(legacy, expected)
    legacy["claims"][1]["protected_conclusion"] = "篡改后的结论"
    claim = dict(legacy["claims"][1])
    claim.pop("claim_fingerprint")
    legacy["claims"][1]["claim_fingerprint"] = value_hash(claim)
    payload = dict(legacy)
    payload.pop("index_hash")
    legacy["index_hash"] = value_hash(payload)
    assert not future_guard_index_matches(legacy, expected)


def test_future_claim_cards_filter_by_position_and_body_hits():
    index = compile_future_guard_index(_chapters())

    cards = future_claim_cards(
        index,
        2,
        "化验确认R-17来自人工增旱阀仓，日期仍待复核。",
    )
    assert [item["claim_id"] for item in cards] == ["event:event-r17-confirmed"]
    assert future_claim_cards(index, 19, "2174年9月21日") == []
    assert future_claim_cards(index, 2) == []

    paraphrase = future_claim_cards(
        index,
        2,
        "检测结论表明，红尘样本的源头就是增旱阀仓。",
    )
    assert [item["claim_id"] for item in paraphrase] == ["event:event-r17-confirmed"]


def test_future_claim_cards_recall_semantic_rewrite_via_protected_object():
    index = compile_future_guard_index(
        _chapters(),
        entities=[
            {
                "id": "sample-r17",
                "kind": "object",
                "name": "R-17",
                "aliases": ["红尘样本"],
            }
        ],
    )

    cards = future_claim_cards(
        index,
        2,
        "试验报告证明红尘样本出自山上的控水设施，而且有人故意散入水源。",
    )

    assert {item["claim_id"] for item in cards} == {
        "event:event-r17-confirmed",
        "milestone:mile-r17-confirmed",
    }


def test_future_claim_cards_do_not_expand_from_visible_character_only():
    chapters = _chapters()
    chapters[1]["future_guard_entity_ids"] = ["char-su-yan"]
    chapters[1]["milestones_consumed"] = []
    index = compile_future_guard_index(
        chapters,
        entities=[{"id": "char-su-yan", "kind": "character", "name": "苏砚"}],
    )

    cards = future_claim_cards(
        index,
        2,
        "他终于弄清真相，幕后缘由与此前猜测完全不同。",
        visible_entity_ids=["char-su-yan"],
    )

    assert cards == []


def test_future_character_name_selects_a_card_for_semantic_audit():
    chapters = _chapters()
    chapters[1]["future_guard_entity_ids"] = ["char-cen-ye"]
    chapters[1]["key_events"] = ["岑野第一次登门提出合作"]
    chapters[1]["milestones_consumed"] = []
    index = compile_future_guard_index(
        chapters,
        entities=[{"id": "char-cen-ye", "kind": "character", "name": "岑野"}],
    )

    cards = future_claim_cards(index, 2, "岑野提前来到村口。")

    assert [item["claim_id"] for item in cards] == ["event:event-r17-confirmed"]


def test_future_claim_cards_do_not_expand_from_current_visible_location():
    chapters = _chapters()
    chapters[1]["future_guard_entity_ids"] = ["loc-north-bay"]
    chapters[1]["milestones_consumed"] = []
    index = compile_future_guard_index(
        chapters,
        entities=[{"id": "loc-north-bay", "kind": "location", "name": "北湾"}],
    )

    assert (
        future_claim_cards(
            index,
            2,
            "沈禾抵达北湾，只记录眼前水车结构。",
            visible_entity_ids=["loc-north-bay"],
        )
        == []
    )


def test_exact_future_conclusion_still_matches_for_visible_entity():
    index = compile_future_guard_index(
        _chapters(),
        entities=[{"id": "sample-r17", "kind": "object", "name": "R-17"}],
    )

    cards = future_claim_cards(
        index,
        2,
        "化验确认R-17来自人工增旱阀仓。",
        visible_entity_ids=["sample-r17"],
    )

    assert [item["claim_id"] for item in cards] == ["event:event-r17-confirmed"]


def test_future_claim_cards_allow_explicit_audit_ids_but_reject_unknown_ids():
    index = compile_future_guard_index(_chapters())
    cards = future_claim_cards(index, 2, claim_ids=["milestone:mile-r17-confirmed"])
    assert [item["kind"] for item in cards] == ["milestone"]
    with pytest.raises(ValueError, match="未知 future claim ID"):
        future_claim_cards(index, 2, claim_ids=["event:missing"])
