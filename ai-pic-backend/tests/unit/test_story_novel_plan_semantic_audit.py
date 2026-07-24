import json

import anyio
import pytest
from app.services.story.story_novel_plan_semantic_audit import (
    _apply_missing_effects,
    _parse_audit,
    audit_and_patch_plan_batch,
)


def _canon():
    return {
        "entities": [
            {"id": "char-wangming", "kind": "character", "name": "王明"},
            {"id": "char-laoguai", "kind": "character", "name": "老拐"},
        ],
        "timeline": [],
        "world_rules": [],
        "milestones": [],
        "character_arcs": [],
        "initial_state": {
            "char-wangming": {"knowledge": []},
            "char-laoguai": {"knowledge": []},
        },
    }


def _chapter():
    return {
        "position": 1,
        "title": "航行中的钟声分析",
        "goal": "分析钟声数据",
        "key_events": [
            "王明确认频率逐年偏移",
            "老拐指出钟声受中央钟塔控制并怀疑人为干预",
        ],
        "character_focus": ["王明", "老拐"],
        "open_threads": [],
        "end_state": "两人提高警惕",
        "min_chars": 3000,
        "target_chars": 4000,
        "max_chars": 5000,
        "length_source": "profile_default",
        "preconditions": [],
        "required_event_ids": ["evt-ch8-1", "evt-ch8-2"],
        "state_transitions": [],
        "knowledge_grants": [],
        "location_transitions": [],
        "milestones_consumed": [],
        "forbidden_event_ids": [],
        "payoffs_due": [],
        "canon_refs": ["char-wangming", "char-laoguai"],
        "timeline_event_bindings": {},
    }


def _six_grants():
    facts = {
        "evt-ch8-1": ["fact-evt-ch8-1-1"],
        "evt-ch8-2": ["fact-evt-ch8-2-1", "fact-evt-ch8-2-2"],
    }
    return [
        {
            "character_id": character_id,
            "fact_id": fact_id,
            "source_event_id": event_id,
        }
        for event_id, fact_ids in facts.items()
        for fact_id in fact_ids
        for character_id in ("char-wangming", "char-laoguai")
    ]


def _audit(grants=None):
    grants = list(grants or [])
    return {
        "events": [
            {
                "position": 1,
                "event_id": event_id,
                "missing_effects": {
                    "knowledge_grants": [
                        item for item in grants if item["source_event_id"] == event_id
                    ],
                    "state_transitions": [],
                    "location_transitions": [],
                    "milestones_consumed": [],
                },
            }
            for event_id in ("evt-ch8-1", "evt-ch8-2")
        ]
    }


def test_ch8_semantic_audit_patches_six_missing_knowledge_grants():
    parsed = _parse_audit(json.dumps(_audit(_six_grants())), _canon(), [_chapter()])

    patched, count = _apply_missing_effects([_chapter()], parsed)

    assert count == 6
    assert patched[0]["knowledge_grants"] == _six_grants()


def test_semantic_audit_requires_exact_event_coverage():
    payload = _audit()
    payload["events"].pop()

    with pytest.raises(ValueError, match="事件覆盖不完整"):
        _parse_audit(json.dumps(payload), _canon(), [_chapter()])


def test_semantic_audit_rejects_extra_event_id():
    payload = _audit()
    payload["events"].append(
        {
            "position": 1,
            "event_id": "evt-future",
            "missing_effects": {},
        }
    )

    with pytest.raises(ValueError, match="事件覆盖不完整"):
        _parse_audit(json.dumps(payload), _canon(), [_chapter()])


def test_semantic_audit_rejects_duplicate_event_id():
    payload = _audit()
    payload["events"][1] = dict(payload["events"][0])

    with pytest.raises(ValueError, match="事件覆盖不完整"):
        _parse_audit(json.dumps(payload), _canon(), [_chapter()])


def test_semantic_audit_rechecks_patched_plan_before_accepting():
    responses = iter((_audit(_six_grants()), _audit()))
    max_tokens = []

    async def generate(_revision, _prompt, **kwargs):
        max_tokens.append(kwargs["max_tokens"])
        return json.dumps(next(responses), ensure_ascii=False)

    async def run():
        return await audit_and_patch_plan_batch(
            object(),
            contract={"story_seed": {"schema": "story_seed_v2"}},
            canon=_canon(),
            prior_chapters=[],
            batch_chapters=[_chapter()],
            require_complete=True,
            generate_text=generate,
        )

    patched = anyio.run(run)

    assert len(patched[0]["knowledge_grants"]) == 6
    assert patched[0]["semantic_audit"]["status"] == "passed"
    assert patched[0]["semantic_audit"]["patched_effect_count"] == 6
    assert max_tokens == [16000, 16000]


def test_semantic_audit_fails_if_second_pass_still_reports_missing_effects():
    responses = iter((_audit(_six_grants()), _audit(_six_grants())))

    async def generate(_revision, _prompt, **_kwargs):
        return json.dumps(next(responses), ensure_ascii=False)

    async def run():
        return await audit_and_patch_plan_batch(
            object(),
            contract={"story_seed": {"schema": "story_seed_v2"}},
            canon=_canon(),
            prior_chapters=[],
            batch_chapters=[_chapter()],
            require_complete=True,
            generate_text=generate,
        )

    with pytest.raises(ValueError, match="返修后仍存在"):
        anyio.run(run)
