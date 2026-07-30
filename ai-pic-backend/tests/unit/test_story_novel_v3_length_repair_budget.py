from app.services.story.story_novel_v3_gate import failed_blocks_for_prose
from app.services.story.story_novel_v3_repair_length import replacement_length_contract


def test_real_chapter_one_repair_preserves_event_bearing_block_capacity():
    blocks = [
        {"block_id": "B01", "content_text": "甲" * 1043},
        {"block_id": "B02", "content_text": "乙" * 1061},
        {"block_id": "B03", "content_text": "丙" * 946},
        {"block_id": "B04", "content_text": "丁" * 884},
    ]
    brief = {
        "beats": [
            {"beat_id": "B01", "target_chars": 600},
            {"beat_id": "B02", "target_chars": 700},
            {"beat_id": "B03", "target_chars": 600},
            {"beat_id": "B04", "target_chars": 600},
        ]
    }
    issue = {
        "reason_code": "length_out_of_range",
        "actual_chars": 3934,
        "min_chars": 2000,
        "target_chars": 2500,
        "max_chars": 3000,
    }

    failed = failed_blocks_for_prose([issue], blocks, brief)
    contract = replacement_length_contract(
        blocks,
        set(failed),
        {"min_chars": 2000, "target_chars": 2500, "max_chars": 3000},
        brief,
    )

    assert failed == ["B01", "B02"]
    assert contract["fixed_chars"] == 1830
    assert contract["repair_model_target_chars"] == 2500
    assert contract["replacement_target_chars"] == 670
    assert [item["target_chars"] for item in contract["replacement_blocks"]] == [
        309,
        361,
    ]
    assert all(item["min_chars"] >= 247 for item in contract["replacement_blocks"])


def test_overlong_selection_expands_until_each_rewritten_beat_has_room():
    blocks = [
        {"block_id": "B01", "content_text": "甲" * 700},
        {"block_id": "B02", "content_text": "乙" * 600},
        {"block_id": "B03", "content_text": "丙" * 600},
        {"block_id": "B04", "content_text": "丁" * 550},
        {"block_id": "B05", "content_text": "戊" * 550},
        {"block_id": "B06", "content_text": "己" * 565},
    ]
    brief = {
        "beats": [
            {"beat_id": f"B{index:02d}", "target_chars": target}
            for index, target in enumerate([420, 420, 420, 420, 410, 410], 1)
        ]
    }
    issue = {
        "reason_code": "length_out_of_range",
        "actual_chars": 3565,
        "min_chars": 2000,
        "target_chars": 2500,
        "max_chars": 3000,
    }

    failed = failed_blocks_for_prose([issue], blocks, brief)

    assert failed == ["B01", "B02", "B03"]
