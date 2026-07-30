import json

import anyio
from app.services.story.story_novel_invocation_evidence import GeneratedNovelText
from app.services.story.story_novel_v3_generation import repair_blocks
from app.services.story.story_novel_v3_prompts import local_block_contract_retry_prompt
from app.services.story.story_novel_v3_repair_input import build_repair_input


def test_length_contract_retry_compresses_previous_replacements_not_old_body():
    calls = []
    blocks = [
        {"block_id": "B01", "content_text": "甲" * 1500},
        {"block_id": "B02", "content_text": "乙" * 1500},
    ]

    async def generate(_revision, prompt, *, stage, **_kwargs):
        calls.append((stage, prompt))
        size = 1500 if len(calls) == 1 else 400
        response = {
            "replacements": [
                {"block_id": "B01", "content_text": "修" * (size - 1) + "。"},
                {"block_id": "B02", "content_text": "补" * (size - 1) + "。"},
            ]
        }
        return GeneratedNovelText(
            json.dumps(response, ensure_ascii=False),
            {"invocation_id": len(calls), "output_tokens": size * 2},
        )

    async def run():
        return await repair_blocks(
            object(),
            1,
            blocks=blocks,
            failed_block_ids=["B01", "B02"],
            violations=[
                {
                    "code": "length_out_of_range",
                    "length_action": "compress",
                    "required_removed_chars": 1000,
                }
            ],
            prose_input={
                "chapter_brief": {
                    "beats": [
                        {"beat_id": "B01", "target_chars": 1000},
                        {"beat_id": "B02", "target_chars": 1000},
                    ]
                },
                "visible_canon": {
                    "chapter_contract": {
                        "position": 1,
                        "timeline_event_bindings": {"time-1": "event-1"},
                    },
                    "compiled_canon": {
                        "timeline": [
                            {
                                "id": "time-1",
                                "story_time": "永和十二年正月十六",
                            }
                        ]
                    },
                },
                "chapter_length": {
                    "min_chars": 1800,
                    "target_chars": 2000,
                    "max_chars": 2500,
                },
            },
            generate_text=generate,
        )

    prose, metrics = anyio.run(run)

    assert prose["char_count"] == 1900
    assert metrics["calls"] == 2
    assert [stage for stage, _prompt in calls] == [
        "local_repair.1",
        "local_repair.1.format_repair",
    ]
    assert calls[1][1].prompt_template["template"] == (
        "story_novel_local_block_repair_v3"
    )
    assert "上一响应未满足正文合同" in calls[1][1]
    assert "previous_replacements_to_compress" in calls[1][1]
    assert "compress_previous_replacements" in calls[1][1]
    assert '"chapter_brief"' not in calls[1][1]
    assert "local repair 合并正文长度为 3000" in calls[1][1]
    assert '"actual_chars":1500' in calls[1][1]
    assert '"max_chars":1200' in calls[1][1]
    assert "修" * 100 in calls[1][1]
    assert "required_literals" not in calls[0][1]
    assert "只修复 JSON 结构，不改变内容语义" not in calls[1][1]
    assert "compress_current_blocks" in calls[0][1]
    assert "甲" * 100 in calls[0][1]
    assert "甲" * 100 not in calls[1][1]


def test_non_length_repair_keeps_source_for_targeted_editing():
    blocks = [{"block_id": "B01", "content_text": "保留这段原文"}]
    repair_input = build_repair_input(
        blocks,
        {"B01"},
        [{"reason_code": "world_rule_violation"}],
        {
            "chapter_brief": {"beats": []},
            "visible_canon": {},
            "chapter_length": {
                "min_chars": 10,
                "target_chars": 20,
                "max_chars": 30,
            },
        },
        {"chapter_min_chars": 10, "chapter_max_chars": 30},
    )

    assert repair_input["failed_blocks"][0]["content_text"] == "保留这段原文"
    assert repair_input["neighbor_blocks"] == []
    assert "rewrite_mode" not in repair_input


def test_short_repair_retry_expands_previous_replacements():
    repair_input = {
        "failed_block_ids": ["B01"],
        "violations": [{"code": "unexpected_claim"}],
        "replacement_length": {
            "fixed_chars": 400,
            "chapter_min_chars": 2000,
            "replacement_blocks": [
                {"block_id": "B01", "min_chars": 1600, "target_chars": 2100}
            ],
        },
    }
    raw = json.dumps(
        {"replacements": [{"block_id": "B01", "content_text": "修" * 1000}]},
        ensure_ascii=False,
    )

    prompt = local_block_contract_retry_prompt(
        repair_input, raw, "local repair 合并正文长度为 1400，必须为 2000–3000"
    )

    assert "expand_previous_replacements" in prompt
    assert "previous_replacements_to_expand" in prompt
    assert '"previous_replacements_to_compress":' not in prompt


def test_underlength_repair_rewrites_from_brief_without_source():
    repair_input = build_repair_input(
        [{"block_id": "B01", "content_text": "过长原文" * 100}],
        {"B01"},
        [{"reason_code": "length_out_of_range"}],
        {
            "chapter_brief": {"beats": [{"beat_id": "B01", "purpose": "守住苗床"}]},
            "current_chapter_context": {
                "events": [{"event_id": "event-9-1", "event": "守住苗床"}]
            },
            "visible_canon": {
                "compiled_canon": {
                    "world_rules": [{"id": "rule-1", "statement": "损失不可消失"}]
                },
                "current_state": {"subjects": {"char-a": {"location": "loc-bed"}}},
            },
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
    assert repair_input["chapter_brief"]["beats"] == [
        {"beat_id": "B01", "purpose": "守住苗床"}
    ]
    assert repair_input["current_chapter_context"]["events"][0]["event"] == "守住苗床"
    assert repair_input["visible_canon"]["compiled_canon"]["world_rules"] == [
        {"id": "rule-1", "statement": "损失不可消失"}
    ]
    assert repair_input["visible_canon"]["current_state"]["subjects"] == {
        "char-a": {"location": "loc-bed"}
    }


def test_repair_neighbors_only_include_read_only_context():
    blocks = [
        {"block_id": "B01", "content_text": "前文"},
        {"block_id": "B02", "content_text": "失败正文"},
        {"block_id": "B03", "content_text": "后文"},
    ]
    repair_input = build_repair_input(
        blocks,
        {"B02"},
        [{"reason_code": "world_rule_violation"}],
        {
            "chapter_brief": {"beats": []},
            "visible_canon": {},
            "chapter_length": {
                "min_chars": 10,
                "target_chars": 20,
                "max_chars": 30,
            },
        },
        {"chapter_min_chars": 10, "chapter_max_chars": 30},
    )

    assert [item["block_id"] for item in repair_input["neighbor_blocks"]] == [
        "B01",
        "B03",
    ]
    assert all(item["editable"] is False for item in repair_input["neighbor_blocks"])


def test_length_repair_neighbors_are_boundary_excerpts_not_copyable_blocks():
    blocks = [
        {"block_id": "B01", "content_text": "前" * 400},
        {"block_id": "B02", "content_text": "旧" * 500},
        {"block_id": "B03", "content_text": "后" * 400},
    ]
    repair_input = build_repair_input(
        blocks,
        {"B02"},
        [{"reason_code": "length_out_of_range"}],
        {
            "chapter_brief": {"beats": [{"beat_id": "B02", "purpose": "推进"}]},
            "visible_canon": {"chapter_contract": {"position": 2}},
            "chapter_length": {
                "min_chars": 500,
                "target_chars": 800,
                "max_chars": 1000,
            },
        },
        {"chapter_min_chars": 500, "chapter_max_chars": 1000},
    )

    assert [item["excerpt"] for item in repair_input["neighbor_blocks"]] == [
        "tail",
        "head",
    ]
    assert [len(item["content_text"]) for item in repair_input["neighbor_blocks"]] == [
        160,
        160,
    ]
