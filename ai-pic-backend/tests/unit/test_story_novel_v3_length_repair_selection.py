import pytest
from app.services.story.story_novel_v3_gate import failed_blocks_for_prose
from app.services.story.story_novel_v3_repair_guidance import deterministic_repair_issue
from app.services.story.story_novel_v3_repair_length import (
    assemble_valid_repair,
    replacement_length_contract,
)


def test_overlong_chapter_repairs_enough_blocks_to_restore_beat_budgets():
    sizes = [700, 600, 600, 550, 550, 565]
    targets = [420, 420, 420, 420, 410, 410]
    blocks = [
        {"block_id": f"B{index:02d}", "content_text": "文" * size}
        for index, size in enumerate(sizes, 1)
    ]
    brief = {
        "beats": [
            {"beat_id": f"B{index:02d}", "target_chars": target}
            for index, target in enumerate(targets, 1)
        ]
    }
    violations = [
        {
            "reason_code": "length_out_of_range",
            "message": "章节长度为 3565，要求 2000–3000",
            "actual_chars": 3565,
            "min_chars": 2000,
            "target_chars": 2500,
            "max_chars": 3000,
        }
    ]

    failed = failed_blocks_for_prose(violations, blocks, brief)
    contract = replacement_length_contract(
        blocks,
        set(failed),
        {"min_chars": 2000, "target_chars": 2500, "max_chars": 3000},
        brief,
    )

    assert failed == ["B01", "B02", "B03"]
    assert contract["fixed_chars"] == 1665
    assert contract["replacement_target_chars"] == 835
    assert contract["repair_safety_margin_chars"] == 125
    assert contract["repair_chapter_ceiling_chars"] == 2875
    assert contract["replacement_max_chars"] == 1210
    assert sum(item["target_chars"] for item in contract["replacement_blocks"]) == 835
    assert contract["replacement_blocks"][0] == {
        "block_id": "B01",
        "original_chars": 700,
        "min_chars": 222,
        "target_chars": 278,
        "max_chars": 333,
    }


def test_real_overlong_shape_keeps_three_usable_blocks_unchanged():
    sizes = [961, 553, 757, 695, 628, 826]
    targets = [400, 400, 300, 500, 400, 500]
    blocks = [
        {"block_id": f"B{index:02d}", "content_text": "文" * size}
        for index, size in enumerate(sizes, 1)
    ]
    brief = {
        "beats": [
            {"beat_id": f"B{index:02d}", "target_chars": target}
            for index, target in enumerate(targets, 1)
        ]
    }

    failed = failed_blocks_for_prose(
        [
            {
                "reason_code": "length_out_of_range",
                "message": "章节长度为 4420，要求 2000–3000",
                "actual_chars": 4420,
                "min_chars": 2000,
                "target_chars": 2500,
                "max_chars": 3000,
            }
        ],
        blocks,
        brief,
    )

    assert failed == ["B01", "B03", "B06"]
    contract = replacement_length_contract(
        blocks,
        set(failed),
        {"min_chars": 2000, "target_chars": 2500, "max_chars": 3000},
        brief,
    )
    assert contract["replacement_target_chars"] == 624


def test_small_overage_selects_enough_blocks_for_a_positive_target():
    sizes = [544, 576, 707, 710, 376, 398]
    targets = [380, 420, 520, 480, 350, 350]
    blocks = [
        {"block_id": f"B{index:02d}", "content_text": "文" * size}
        for index, size in enumerate(sizes, 1)
    ]
    brief = {
        "beats": [
            {"beat_id": f"B{index:02d}", "target_chars": target}
            for index, target in enumerate(targets, 1)
        ]
    }

    failed = failed_blocks_for_prose(
        [
            {
                "reason_code": "length_out_of_range",
                "message": "章节长度为 3311，要求 2000–3000",
                "actual_chars": 3311,
                "min_chars": 2000,
                "target_chars": 2500,
                "max_chars": 3000,
            }
        ],
        blocks,
        brief,
    )
    contract = replacement_length_contract(
        blocks,
        set(failed),
        {"min_chars": 2000, "target_chars": 2500, "max_chars": 3000},
        brief,
    )

    assert failed == ["B03", "B04"]
    assert contract["fixed_chars"] == 1894
    assert contract["replacement_target_chars"] == 606


def test_overlong_repair_guidance_requires_an_explicit_character_reduction():
    issue = deterministic_repair_issue(
        {
            "reason_code": "length_out_of_range",
            "actual_chars": 3565,
            "min_chars": 2000,
            "target_chars": 2500,
            "max_chars": 3000,
        }
    )

    assert issue["length_action"] == "compress"
    assert issue["required_removed_chars"] == 1065
    assert "至少删除 1065" in issue["length_instruction"]


def test_repair_accepts_block_variance_when_merged_length_is_valid():
    blocks = [
        {"block_id": "B01", "content_text": "甲" * 1500},
        {"block_id": "B02", "content_text": "乙" * 1500},
    ]
    contract = replacement_length_contract(
        blocks,
        {"B01", "B02"},
        {"min_chars": 1800, "target_chars": 2000, "max_chars": 2500},
        {
            "beats": [
                {"beat_id": "B01", "target_chars": 1000},
                {"beat_id": "B02", "target_chars": 1000},
            ]
        },
    )

    result = assemble_valid_repair(
        blocks,
        [
            {"block_id": "B01", "content_text": "修" * 699 + "。"},
            {"block_id": "B02", "content_text": "补" * 1299 + "。"},
        ],
        contract,
    )

    assert result["char_count"] == 2000


def test_repair_rejects_an_empty_block_even_when_merged_length_is_valid():
    blocks = [
        {"block_id": "B01", "content_text": "甲" * 1000},
        {"block_id": "B02", "content_text": "乙" * 1000},
    ]
    contract = replacement_length_contract(
        blocks,
        {"B01", "B02"},
        {"min_chars": 1000, "target_chars": 1500, "max_chars": 2000},
    )

    with pytest.raises(ValueError, match="B01"):
        assemble_valid_repair(
            blocks,
            [
                {"block_id": "B01", "content_text": ""},
                {"block_id": "B02", "content_text": "补" * 1500},
            ],
            contract,
        )


def test_repair_rejects_copying_a_long_neighbor_paragraph():
    paragraph = "这是一段不得复制的相邻正文。" * 10
    blocks = [
        {"block_id": "B01", "content_text": paragraph},
        {"block_id": "B02", "content_text": "旧" * 100},
    ]
    contract = replacement_length_contract(
        blocks,
        {"B02"},
        {"min_chars": 100, "target_chars": 300, "max_chars": 500},
    )

    with pytest.raises(ValueError, match="重复了 B01"):
        assemble_valid_repair(
            blocks,
            [{"block_id": "B02", "content_text": paragraph}],
            contract,
        )


def test_second_repair_rejects_overlong_blocks_instead_of_mechanical_chopping():
    fixed = "固定首稿。" * 250
    blocks = [
        {"block_id": "B01", "content_text": fixed},
        {
            "block_id": "B02",
            "content_text": "开头行动。" + "过程推进。" * 90 + "结尾钩子。",
        },
        {
            "block_id": "B03",
            "content_text": "冲突出现。" + "反复交锋。" * 90 + "代价落定。",
        },
    ]
    contract = replacement_length_contract(
        blocks,
        {"B02", "B03"},
        {"min_chars": 1000, "target_chars": 1500, "max_chars": 1800},
    )

    with pytest.raises(ValueError, match="local repair 合并正文长度"):
        assemble_valid_repair(blocks, blocks[1:], contract)
