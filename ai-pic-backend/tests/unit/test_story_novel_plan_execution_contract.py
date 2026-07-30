import json
from types import SimpleNamespace

import anyio
import pytest
from app.services.story.story_novel_plan_semantic_audit import (
    _parse_audit,
    audit_and_patch_plan_batch,
)
from tests.unit.test_story_novel_plan_semantic_audit import _audit, _canon, _chapter


def _run_with_issues(issues, action_phase=None):
    async def generate(_revision, _prompt, **_kwargs):
        payload = _audit(issues=issues)
        if action_phase:
            payload["events"][0]["execution_contract"]["action_phase"] = action_phase
        return json.dumps(payload, ensure_ascii=False)

    async def run():
        return await audit_and_patch_plan_batch(
            SimpleNamespace(generation_plan={}),
            contract={"story_seed": {"schema": "story_seed_v2"}},
            canon=_canon(),
            prior_chapters=[],
            batch_chapters=[_chapter()],
            require_complete=True,
            generate_text=generate,
        )

    return anyio.run(run)


def test_semantic_audit_blocks_only_direct_execution_conflicts():
    blocking = {
        "evt-ch8-1": [
            {
                "code": "timeline_duration_conflict",
                "severity": "advisory",
                "message": "固定同日事件与明确三日工期冲突",
            }
        ]
    }

    with pytest.raises(ValueError, match="章节计划不可执行.*timeline_duration"):
        _run_with_issues(blocking)


def test_semantic_audit_keeps_web_fiction_plausibility_as_advisory():
    advisory = {
        "evt-ch8-1": [
            {
                "code": "labor_feasibility",
                "severity": "blocking",
                "message": "动作较快但原事件没有明示工程规模",
            }
        ]
    }

    chapter = _run_with_issues(advisory)[0]

    assert chapter["semantic_audit"]["status"] == "passed"
    assert (
        chapter["semantic_audit"]["execution_advisories"][0]["severity"] == "advisory"
    )


def test_semantic_audit_keeps_effect_event_attribution_as_advisory():
    advisory = {
        "evt-ch8-1": [
            {
                "code": "effect_event_attribution",
                "severity": "blocking",
                "message": "章节净状态应归属同章另一事件",
            }
        ]
    }

    chapter = _run_with_issues(advisory)[0]

    assert chapter["semantic_audit"]["status"] == "passed"
    assert chapter["semantic_audit"]["execution_advisories"][0]["code"] == (
        "effect_event_attribution"
    )


def test_execution_audit_prompt_keeps_unscoped_labor_non_blocking():
    from app.services.story.story_novel_plan_semantic_audit import _audit_prompt

    prompt = _audit_prompt({}, _canon(), [], [_chapter()])

    assert "effort 必须为 unspecified" in prompt
    assert "一般写实程度、劳动略快、戏剧化巧合" in prompt
    assert "只能标 advisory" in prompt
    assert "effect_event_attribution advisory" in prompt


def test_execution_actor_must_be_a_current_chapter_character():
    canon = _canon()
    canon["entities"].append({"id": "loc-field", "kind": "location", "name": "田地"})
    payload = _audit()
    payload["events"][0]["execution_contract"]["actor_ids"] = ["loc-field"]

    with pytest.raises(ValueError, match="actor 引用无效"):
        _parse_audit(json.dumps(payload), canon, [_chapter()])


def test_execution_actor_can_be_current_chapter_organization():
    canon = _canon()
    canon["entities"].append(
        {
            "id": "org-cooperative",
            "kind": "organization",
            "name": "柳溪合作社",
            "aliases": [],
        }
    )
    chapter = _chapter()
    chapter["key_events"] = ["合作社决定建造小仓缓售"]
    payload = _audit()
    payload["events"][0]["execution_contract"]["actor_ids"] = [
        "char-wangming",
        "org-cooperative",
    ]

    parsed = _parse_audit(json.dumps(payload), canon, [chapter])

    assert parsed[0]["execution_contract"]["actor_ids"] == [
        "char-wangming",
        "org-cooperative",
    ]


def test_execution_actor_drops_canon_character_not_bound_to_current_chapter():
    chapter = _chapter()
    chapter["key_events"] = ["王明确认频率逐年偏移"]
    chapter["character_focus"] = ["王明"]
    chapter["canon_refs"] = ["char-wangming"]
    payload = _audit()
    payload["events"][0]["execution_contract"]["actor_ids"] = [
        "char-wangming",
        "char-laoguai",
    ]

    parsed = _parse_audit(json.dumps(payload), _canon(), [chapter])

    assert parsed[0]["execution_contract"]["actor_ids"] == ["char-wangming"]


def test_execution_event_id_is_bound_from_validated_outer_event():
    payload = _audit()
    payload["events"][0]["execution_contract"].pop("event_id")

    parsed = _parse_audit(json.dumps(payload), _canon(), [_chapter()])

    assert parsed[0]["execution_contract"]["event_id"] == "evt-ch8-1"


def test_execution_event_id_mismatch_remains_invalid():
    payload = _audit()
    payload["events"][0]["execution_contract"]["event_id"] = "evt-other"

    with pytest.raises(ValueError, match="execution event_id 无效"):
        _parse_audit(json.dumps(payload), _canon(), [_chapter()])


def test_execution_actor_can_be_bound_by_current_typed_subjects_and_values():
    chapter = _chapter()
    chapter["canon_refs"] = []
    chapter["character_focus"] = []
    chapter["key_events"] = ["确认频率偏移", "指出中央钟塔控制"]
    chapter["preconditions"] = [
        {
            "subject_id": "char-wangming",
            "field": "partner_id",
            "operator": "eq",
            "value": "char-laoguai",
        }
    ]
    grant = {
        "character_id": "char-wangming",
        "fact_id": "fact-evt-ch8-1-1",
        "source_event_id": "evt-ch8-1",
    }
    chapter["knowledge_grants"] = [grant]
    payload = _audit(existing_grants=[grant])
    payload["events"][0]["execution_contract"]["actor_ids"] = [
        "char-wangming",
        "char-laoguai",
    ]

    parsed = _parse_audit(json.dumps(payload), _canon(), [chapter])

    assert parsed[0]["execution_contract"]["actor_ids"] == [
        "char-wangming",
        "char-laoguai",
    ]


def test_execution_actor_can_be_bound_by_current_focus_name():
    chapter = _chapter()
    chapter["canon_refs"] = []

    parsed = _parse_audit(json.dumps(_audit()), _canon(), [chapter])

    assert parsed[0]["execution_contract"]["actor_ids"] == ["char-wangming"]


def test_execution_contract_deduplicates_same_fact_for_multiple_characters():
    chapter = _chapter()
    fact_id = "fact-evt-ch8-1-1"
    grants = [
        {
            "character_id": character_id,
            "fact_id": fact_id,
            "source_event_id": "evt-ch8-1",
        }
        for character_id in ("char-wangming", "char-laoguai")
    ]
    chapter["knowledge_grants"] = grants
    payload = _audit(existing_grants=grants)
    payload["events"][0]["execution_contract"]["knowledge_fact_ids"] = ["stale"]
    payload["events"][0]["execution_contract"]["timeline_ids"] = ["stale-time"]

    parsed = _parse_audit(json.dumps(payload), _canon(), [chapter])

    assert parsed[0]["execution_contract"]["knowledge_fact_ids"] == [fact_id]
    assert parsed[0]["execution_contract"]["timeline_ids"] == []
