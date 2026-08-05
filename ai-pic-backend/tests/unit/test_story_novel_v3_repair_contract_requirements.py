import json

from app.services.story.story_novel_v3_prompts import local_block_contract_retry_prompt
from app.services.story.story_novel_v3_repair_guidance import (
    deterministic_repair_issue,
    safe_repair_issues,
)
from app.services.story.story_novel_v3_repair_input import build_repair_input


def _repair_input():
    brief = {
        "beats": [
            {
                "beat_id": "B04",
                "bound_event_ids": ["event-9-2"],
                "effect_contract_ids": ["location:3"],
            },
            {
                "beat_id": "B05",
                "bound_event_ids": ["event-9-3"],
                "effect_contract_ids": [],
            },
        ]
    }
    return build_repair_input(
        [{"block_id": "B04", "content_text": "旧正文"}],
        {"B04"},
        [{"code": "unexpected_claim", "sentence_ids": ["S0059"]}],
        {
            "chapter_brief": brief,
            "current_chapter_context": {
                "events": [{"event_id": "event-9-2", "event": "清点冻损"}]
            },
            "visible_canon": {},
            "chapter_length": {},
        },
        {
            "replacement_blocks": [
                {
                    "block_id": "B04",
                    "original_chars": 3,
                    "min_chars": 2,
                    "target_chars": 3,
                    "max_chars": 4,
                }
            ],
            "fixed_chars": 2000,
            "chapter_min_chars": 2000,
            "chapter_max_chars": 3000,
            "replacement_min_chars": 2,
            "replacement_target_chars": 3,
            "replacement_max_chars": 4,
        },
        {
            "proof_contracts": [
                {
                    "contract_id": "event:event-9-2",
                    "kind": "event",
                    "value": "event-9-2",
                },
                {
                    "contract_id": "location:3",
                    "kind": "location_transition",
                    "value": {
                        "subject_id": "char-shenhe",
                        "from_location_id": "loc-south-slope-field",
                        "to_location_id": "loc-old-house",
                        "means": "清点完损失后返回旧屋",
                    },
                },
                {
                    "contract_id": "event:event-9-3",
                    "kind": "event",
                    "value": "event-9-3",
                },
            ]
        },
    )


def test_failed_beat_receives_only_its_current_typed_contracts():
    repair_input = _repair_input()

    assert repair_input["current_contract_requirements"] == {
        "scope": "current_chapter_only",
        "proof_contracts": [
            {
                "contract_id": "event:event-9-2",
                "kind": "event",
                "value": "event-9-2",
            },
            {
                "contract_id": "location:3",
                "kind": "location_transition",
                "value": {
                    "subject_id": "char-shenhe",
                    "from_location_id": "loc-south-slope-field",
                    "to_location_id": "loc-old-house",
                    "means": "清点完损失后返回旧屋",
                },
            },
        ],
    }


def test_failed_beat_does_not_receive_other_beat_events_or_actors():
    brief = {
        "beats": [
            {
                "beat_id": "B01",
                "bound_event_ids": ["event-10-1"],
                "allowed_entity_ids": ["char-chen"],
            },
            {
                "beat_id": "B02",
                "bound_event_ids": ["event-10-2"],
                "allowed_entity_ids": ["char-dongfang"],
            },
        ]
    }
    repair_input = build_repair_input(
        [
            {"block_id": "B01", "content_text": "短"},
            {"block_id": "B02", "content_text": "保留正文"},
        ],
        {"B01"},
        [{"reason_code": "length_out_of_range", "length_action": "expand"}],
        {
            "chapter_brief": brief,
            "current_chapter_context": {
                "events": [
                    {
                        "event_id": "event-10-1",
                        "event": "陈禾确认减收",
                        "execution": {"actor_ids": ["char-chen"]},
                        "scene_participants": [],
                    },
                    {
                        "event_id": "event-10-2",
                        "event": "东方浪铲去弱苗",
                        "execution": {"actor_ids": ["char-dongfang"]},
                        "scene_participants": [],
                    },
                ],
                "characters": [
                    {"id": "char-chen", "name": "陈禾"},
                    {"id": "char-dongfang", "name": "东方浪"},
                ],
                "scene_participants": [],
                "typed_execution_boundary": {"effects_are_exhaustive": True},
            },
            "visible_canon": {},
            "chapter_length": {
                "min_chars": 2000,
                "target_chars": 2500,
                "max_chars": 3000,
            },
        },
        {"chapter_min_chars": 2000, "chapter_max_chars": 3000},
    )

    context = repair_input["current_chapter_context"]
    assert [item["event_id"] for item in context["events"]] == ["event-10-1"]
    assert [item["id"] for item in context["characters"]] == ["char-chen"]
    assert "typed_execution_boundary" not in context


def test_length_retry_keeps_current_effect_without_audit_free_text():
    repair_input = _repair_input()
    repair_input["violations"][0]["message"] = "不得发送给正文模型的审计自由文本"
    previous = {"replacements": [{"block_id": "B04", "content_text": "过长正文"}]}

    prompt = local_block_contract_retry_prompt(
        repair_input,
        json.dumps(previous, ensure_ascii=False),
        "local repair 合并正文长度超限；请严格遵守 replacement_length",
    )

    assert "清点完损失后返回旧屋" in prompt
    assert "清点冻损" in prompt
    assert "不得发送给正文模型的审计自由文本" not in prompt


def test_named_entity_repair_keeps_only_current_contract_name():
    issue = deterministic_repair_issue(
        {
            "code": "canon_violation",
            "reason_code": "entity_introduction_name_missing",
            "message": "模型自由文本不得进入正文修复",
            "entity_id": "char-zhou",
            "required_names": ["周谨"],
            "block_ids": ["B03"],
        }
    )

    assert safe_repair_issues([issue]) == [
        {
            "code": "entity_introduction_name_missing",
            "entity_id": "char-zhou",
            "required_names": ["周谨"],
            "block_ids": ["B03"],
        }
    ]
