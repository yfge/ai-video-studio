import json

from app.services.story.story_novel_v3_prompts import local_block_contract_retry_prompt
from app.services.story.story_novel_v3_repair_length import replacement_length_contract


def test_duplicate_retry_only_revises_prior_replacements():
    repair_input = {
        "failed_block_ids": ["B03"],
        "failed_blocks": [{"block_id": "B03", "content_text": "旧错误正文"}],
        "chapter_brief": {"beats": [{"beat_id": "B03"}]},
        "current_chapter_context": {
            "events": [{"event": "修补旧屋"}],
            "scene_participants": [
                {
                    "label": "家人",
                    "scope": "current_chapter_only",
                    "persistent_state": False,
                }
            ],
        },
        "violations": [
            {
                "code": "unexpected_claim",
                "message": "未来章节才允许出现的秘密",
                "sentence_ids": ["S0007"],
            }
        ],
        "neighbor_blocks": [
            {"block_id": "B04", "content_text": "固定邻块", "editable": False}
        ],
        "replacement_length": {
            "fixed_chars": 400,
            "chapter_min_chars": 2000,
            "replacement_blocks": [
                {"block_id": "B03", "min_chars": 500, "target_chars": 650}
            ],
        },
        "visible_canon": {},
        "writing_style": {},
    }
    raw = json.dumps(
        {"replacements": [{"block_id": "B03", "content_text": "待修正文"}]},
        ensure_ascii=False,
    )

    prompt = local_block_contract_retry_prompt(
        repair_input, raw, "B04 重复了 B03 的长段正文"
    )

    assert "repair_previous_replacements" in prompt
    assert "previous_response_to_revise" in prompt
    assert "必须删除全部重叠句段" in prompt
    assert "固定邻块" in prompt
    assert "家人" in prompt
    assert "current_chapter_only" in prompt
    assert "旧错误正文" not in prompt
    assert "未来章节才允许出现的秘密" not in prompt
    assert "S0007" in prompt
    assert '"chapter_brief"' not in prompt


def test_audit_repair_overage_retries_as_compression_with_block_budgets():
    blocks = [
        {"block_id": "B01", "content_text": "甲" * 700},
        {"block_id": "B02", "content_text": "固" * 850},
        {"block_id": "B03", "content_text": "乙" * 370},
        {"block_id": "B04", "content_text": "定" * 909},
    ]
    brief = {
        "beats": [
            {"beat_id": "B01", "target_chars": 600},
            {"beat_id": "B02", "target_chars": 800},
            {"beat_id": "B03", "target_chars": 400},
            {"beat_id": "B04", "target_chars": 700},
        ]
    }
    contract = replacement_length_contract(
        blocks,
        {"B01", "B03"},
        {"min_chars": 2000, "target_chars": 2500, "max_chars": 3000},
        brief,
    )
    response = json.dumps(
        {
            "replacements": [
                {"block_id": "B01", "content_text": "修" * 635},
                {"block_id": "B03", "content_text": "补" * 639},
            ]
        },
        ensure_ascii=False,
    )
    repair_input = {
        "failed_block_ids": ["B01", "B03"],
        "replacement_length": contract,
        "current_chapter_context": {},
        "violations": [],
        "neighbor_blocks": [],
        "visible_canon": {},
        "writing_style": {},
    }

    prompt = local_block_contract_retry_prompt(
        repair_input,
        response,
        "local repair 合并正文长度为 3033，必须为 2000–3000",
    )

    assert contract["fixed_chars"] == 1759
    assert [item["block_id"] for item in contract["replacement_blocks"]] == [
        "B01",
        "B03",
    ]
    assert "compress_previous_replacements" in prompt
    assert '"actual_chars":635' in prompt
    assert '"actual_chars":639' in prompt
    assert contract["replacement_target_chars"] == 741
    assert '"retry_source_actual_chars":1274' in prompt
    assert '"retry_model_target_chars":431' in prompt
    assert '"replacement_target_chars":431' in prompt
