import json

from app.services.story.story_novel_plan_semantic_audit import _apply_missing_effects
from app.services.story.story_novel_plan_semantic_effects import (
    remove_unsupported_effects,
)
from app.services.story.story_novel_plan_semantic_prompt import (
    build_plan_semantic_audit_prompt,
)


def test_semantic_audit_exposes_absent_entity_aliases_and_first_use_rule():
    canon = {
        "entities": [
            {
                "id": "obj-ledger",
                "kind": "object",
                "name": "共同账本",
                "aliases": ["共同账", "账页"],
            },
        ],
        "timeline": [],
        "world_rules": [],
        "milestones": [],
        "initial_state": {
            "obj-ledger": {"status": "not-yet-created", "location": None}
        },
    }
    chapter = {
        "position": 5,
        "key_events": ["两人把共同开支写进共同账"],
        "character_focus": [],
        "required_event_ids": ["event-5-1"],
        "state_transitions": [],
        "knowledge_grants": [],
        "location_transitions": [],
        "milestones_consumed": [],
        "end_state": "共同开支已有书面记录",
        "timeline_event_bindings": {},
    }

    prompt = build_plan_semantic_audit_prompt({}, canon, [], [chapter])
    payload = json.loads(prompt.split("输入：", 1)[1])

    assert payload["canon_entities"][0]["aliases"] == ["共同账", "账页"]
    assert payload["entity_lifecycle_contract"]["initially_absent_entities"] == [
        {
            "subject_id": "obj-ledger",
            "kind": "object",
            "name": "共同账本",
            "aliases": ["共同账", "账页"],
            "initial_status": "not-yet-created",
        }
    ]
    assert "首次实际使用事件所在章补入唯一的 status 创建转换" in prompt
    assert "更晚章节不得再次从不存在开始" in prompt


def test_semantic_lifecycle_patch_replaces_late_first_creation():
    early = {"position": 5, "required_event_ids": ["event-5-1"]}
    late_creation = {
        "subject_id": "obj-ledger",
        "field": "status",
        "from_value": "not-yet-created",
        "to_value": "formalized",
        "reason": "错误地延后首次创建",
    }
    late = {
        "position": 9,
        "required_event_ids": ["event-9-1"],
        "state_transitions": [late_creation],
    }
    early_creation = {
        **late_creation,
        "to_value": "provisional",
        "reason": "首次实际使用",
    }
    later_upgrade = {
        **late_creation,
        "from_value": "provisional",
        "reason": "从当前状态升级",
    }
    empty = {
        "knowledge_grants": [],
        "state_transitions": [],
        "location_transitions": [],
        "milestones_consumed": [],
    }
    audit = [
        {
            "position": 5,
            "event_id": "event-5-1",
            "missing_effects": {**empty, "state_transitions": [early_creation]},
            "unsupported_effects": empty,
        },
        {
            "position": 9,
            "event_id": "event-9-1",
            "missing_effects": {**empty, "state_transitions": [later_upgrade]},
            "unsupported_effects": {
                **empty,
                "state_transitions": [late_creation],
            },
        },
    ]

    patched, added = _apply_missing_effects([early, late], audit)
    patched, removed = remove_unsupported_effects(patched, audit)

    assert (added, removed) == (2, 1)
    assert patched[0]["state_transitions"] == [early_creation]
    assert patched[1]["state_transitions"] == [later_upgrade]
