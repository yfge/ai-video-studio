from types import SimpleNamespace

from app.services.story.story_novel_continuity_contract import continuity_prompt
from app.services.story.story_novel_continuity_grounding import (
    chapter_evidence_catalog,
    contract_reference_catalog,
    payload_evidence_catalog,
)
from app.services.story.story_novel_continuity_review import window_payload


def test_window_payload_uses_stable_sentence_index_instead_of_raw_duplicate_body():
    chapter = SimpleNamespace(
        business_id="chapter-1",
        content_hash="body-hash",
        position=1,
        title="开荒",
        content_text="沈禾量完三亩地。顾砚记下水位。",
    )
    revision = SimpleNamespace(
        story_snapshot={
            "title": "开荒记",
            "characters": [{"name": "旧档案人物", "background": "冲突旧背景"}],
            "story_seed": {"title": "开荒记", "target_audience": "连载读者"},
        },
        generation_plan={
            "canon": {
                "entities": [
                    {
                        "id": "char-shenhe",
                        "kind": "character",
                        "attributes": {"gender": "female"},
                    }
                ],
                "initial_state": {"char-shenhe": {"location": "loc-field"}},
            },
            "chapters": [{"position": 1, "required_event_ids": ["event-1"]}],
        },
    )

    payload = window_payload(
        revision,
        [chapter],
        {
            "1": {
                "state_delta": {"occurred_event_ids": ["event-1"]},
                "state_validation": {"status": "passed"},
            }
        },
    )
    row = payload["chapters"][0]

    assert "content" not in row
    assert [item["sentence_id"] for item in row["sentence_index"]] == [
        "S0001",
        "S0002",
    ]
    assert row["sentence_index_hash"]
    assert chapter_evidence_catalog([chapter]) == {"chapter-1": {"S0001", "S0002"}}
    assert "canon:entity:char-shenhe:attributes.gender" in set(
        payload["valid_contract_refs"]
    )
    assert contract_reference_catalog(revision, [chapter]) >= {
        "chapter:chapter-1:contract",
        "canon:initial_state:char-shenhe:location",
    }
    assert "characters" not in payload["story_contract"]
    assert payload["story_contract"]["story_seed_invariants"]["title"] == "开荒记"
    assert row["checkpoint"]["state_delta"]["occurred_event_ids"] == ["event-1"]
    assert payload["state_chain_contract"]["state_before"].startswith("章节开始前")


def test_global_prompt_requires_grounding_without_auto_approval():
    prompt = continuity_prompt(
        "全局检查", {"chapters": []}, issue_limit=40, include_editorial=True
    )

    assert "overall_score >= 75" in prompt
    assert "blocking_issues 为空" in prompt
    assert "evidence_refs" in prompt
    assert "缺少上述可验证证据的问题只能标 warning" in prompt
    assert "不得据此\n输出审批结论或自动批准" in prompt


def test_global_proof_refs_without_sentence_text_do_not_authorize_blocking_evidence():
    payload = {
        "chapters": [
            {
                "business_id": "chapter-1",
                "sentence_index": [{"sentence_id": "S0001", "text": "已提供正文"}],
                "proof_refs": {"event:event-1": ["S0001", "S9999"]},
            }
        ]
    }

    assert payload_evidence_catalog(payload) == {"chapter-1": {"S0001"}}
