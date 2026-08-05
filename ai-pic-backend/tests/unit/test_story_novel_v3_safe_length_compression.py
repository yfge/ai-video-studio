from app.services.story.story_novel_v3_repair_input import build_repair_input


def test_pure_overlength_repair_compresses_existing_safe_blocks():
    blocks = [
        {"block_id": "B01", "content_text": "保留事件顺序。" * 220},
        {"block_id": "B02", "content_text": "只删除重复表达。" * 220},
    ]
    prose_input = {
        "chapter_brief": {
            "beats": [
                {"beat_id": "B01", "purpose": "得知门槛"},
                {"beat_id": "B02", "purpose": "开始准备"},
            ]
        },
        "current_chapter_context": {
            "typed_execution_boundary": {
                "effects_are_exhaustive": True,
                "location_transitions": [],
                "unchanged_location_subject_ids": ["char-a", "char-b"],
            }
        },
        "visible_canon": {},
        "chapter_length": {
            "min_chars": 2000,
            "target_chars": 2500,
            "max_chars": 3000,
        },
    }

    result = build_repair_input(
        blocks,
        {"B01", "B02"},
        [
            {
                "reason_code": "length_out_of_range",
                "length_action": "compress",
                "actual_chars": 3080,
                "max_chars": 3000,
            }
        ],
        prose_input,
        {
            "chapter_min_chars": 2000,
            "chapter_max_chars": 3000,
            "replacement_blocks": [],
        },
    )

    assert result["rewrite_mode"] == "compress_current_blocks"
    assert result["failed_blocks"] == blocks
    assert result["current_chapter_context"]["typed_execution_boundary"][
        "unchanged_location_subject_ids"
    ] == ["char-a", "char-b"]
    assert result["chapter_brief"]["beats"] == prose_input["chapter_brief"]["beats"]
    assert "重新创作" in result["length_rewrite_instruction"]


def test_mixed_content_failure_keeps_targeted_source_without_length_mode():
    blocks = [{"block_id": "B01", "content_text": "当前安全正文"}]

    result = build_repair_input(
        blocks,
        {"B01"},
        [
            {"reason_code": "length_out_of_range", "length_action": "compress"},
            {"reason_code": "world_rule_violation"},
        ],
        {
            "chapter_brief": {"beats": [{"beat_id": "B01"}]},
            "current_chapter_context": {},
            "visible_canon": {},
            "chapter_length": {
                "min_chars": 10,
                "target_chars": 20,
                "max_chars": 30,
            },
        },
        {
            "chapter_min_chars": 10,
            "chapter_max_chars": 30,
            "replacement_blocks": [],
        },
    )

    assert result["failed_blocks"] == blocks
    assert "rewrite_mode" not in result
