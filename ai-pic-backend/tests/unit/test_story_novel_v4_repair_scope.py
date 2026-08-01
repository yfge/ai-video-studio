from app.services.story.story_novel_v3_prompts import local_block_repair_prompt
from app.services.story.story_novel_v3_repair_input import build_repair_input


def test_v4_underlength_repair_uses_beat_without_cross_block_event_text():
    repair_input = build_repair_input(
        [{"block_id": "B01", "content_text": "原文" * 100}],
        {"B01"},
        [{"reason_code": "length_out_of_range"}],
        {
            "schema": "story_novel_prose_packet.v2",
            "chapter_brief": {
                "beats": [
                    {
                        "beat_id": "B01",
                        "purpose": "修尺、理绳并统一量法",
                        "bound_event_ids": ["E01"],
                    }
                ]
            },
            "current_chapter_context": {
                "events": [
                    {
                        "event_id": "E01",
                        "event": "修尺后继续量完整块之外的田界并划分四区",
                    }
                ]
            },
            "visible_canon": {"characters": [], "world": []},
            "chapter_length": {
                "min_chars": 2000,
                "target_chars": 2500,
                "max_chars": 3000,
            },
        },
        {
            "chapter_min_chars": 2000,
            "chapter_max_chars": 3000,
            "replacement_blocks": [],
        },
    )

    assert repair_input["rewrite_mode"] == "length_contract_from_chapter_brief"
    assert "content_text" not in repair_input["failed_blocks"][0]
    assert repair_input["chapter_brief"]["beats"][0]["purpose"] == (
        "修尺、理绳并统一量法"
    )
    assert repair_input["current_chapter_context"]["events"] == [{"event_id": "E01"}]
    assert repair_input["current_contract_requirements"] == {
        "scope": "current_blocks_only",
        "event_handles": ["E01"],
    }


def test_v4_repair_allows_event_named_transient_group_to_fulfil_action():
    prose_input = {
        "schema": "story_novel_prose_packet.v2",
        "chapter_brief": {
            "beats": [
                {
                    "beat_id": "B03",
                    "purpose": "完成约定留痕",
                    "bound_event_ids": ["E02"],
                }
            ]
        },
        "current_chapter_context": {
            "events": [
                {
                    "event_id": "E02",
                    "event": "顾砚、顾承宗及相邻用水户在约定上留名见证",
                    "execution": {"actor_ids": []},
                    "scene_participants": [],
                }
            ]
        },
        "visible_canon": {"characters": [], "world": []},
        "chapter_length": {
            "min_chars": 2000,
            "target_chars": 2500,
            "max_chars": 3000,
        },
    }
    repair_input = build_repair_input(
        [{"block_id": "B03", "content_text": "相邻用水户只旁观，三人留名。"}],
        {"B03"},
        [
            {
                "code": "unexpected_claim",
                "sentence_ids": ["S0030"],
                "spans": [{"sentence_id": "S0030", "text": "三人留名。"}],
            }
        ],
        prose_input,
        {
            "replacement_blocks": [
                {
                    "block_id": "B03",
                    "original_chars": 16,
                    "min_chars": 12,
                    "target_chars": 16,
                    "max_chars": 24,
                }
            ],
            "chapter_min_chars": 2000,
            "chapter_max_chars": 3000,
        },
    )

    prompt = local_block_repair_prompt(repair_input)

    assert "匿名群体或职能角色也可作为" in prompt
    assert "transient 参与者" in prompt
    assert "不得把应当参与或留痕的人改写为只旁观" in prompt
    assert "顾砚、顾承宗及相邻用水户在约定上留名见证" in prompt
