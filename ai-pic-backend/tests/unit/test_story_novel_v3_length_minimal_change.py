import json

from app.services.story.story_novel_v3_repair_length import (
    repair_response_parser,
    replacement_length_contract,
)


def _blocks():
    return [
        {"block_id": f"B{index:02d}", "content_text": token * (size - 1) + "。"}
        for index, (token, size) in enumerate(
            zip("甲乙丙丁戊己", (402, 497, 527, 578, 593, 575), strict=True), 1
        )
    ]


def _response():
    return json.dumps(
        {
            "replacements": [
                {"block_id": "B04", "content_text": "修" * 299 + "。"},
                {"block_id": "B05", "content_text": "补" * 299 + "。"},
            ]
        },
        ensure_ascii=False,
    )


def _contract(violations):
    return replacement_length_contract(
        _blocks(),
        {"B04", "B05"},
        {"min_chars": 2000, "target_chars": 2500, "max_chars": 3000},
        violations=violations,
    )


def test_pure_length_repair_replaces_every_failed_block_when_valid():
    contract = _contract([{"reason_code": "length_out_of_range"}])

    result = repair_response_parser(_blocks(), {"B04", "B05"}, contract)(_response())
    by_id = {
        item["block_id"]: item["content_text"] for item in result["block_contents"]
    }

    assert contract["selection_policy"] == "complete_failed_blocks_first_v2"
    assert result["char_count"] == 2601
    assert by_id["B04"] == "修" * 299 + "。"
    assert by_id["B05"] == "补" * 299 + "。"


def test_content_repair_still_replaces_every_failed_block():
    contract = _contract([{"reason_code": "unexpected_claim"}])

    result = repair_response_parser(_blocks(), {"B04", "B05"}, contract)(_response())
    by_id = {
        item["block_id"]: item["content_text"] for item in result["block_contents"]
    }

    assert "selection_policy" not in contract
    assert result["char_count"] == 2601
    assert by_id["B04"] == "修" * 299 + "。"
    assert by_id["B05"] == "补" * 299 + "。"


def test_retry_uses_all_calibrated_replacements_when_they_fit():
    blocks = [
        {"block_id": f"B{index:02d}", "content_text": token * (size - 1) + "。"}
        for index, (token, size) in enumerate(
            zip("甲乙丙丁戊己", (552, 590, 580, 537, 618, 667), strict=True), 1
        )
    ]
    failed = {"B02", "B05", "B06"}
    contract = replacement_length_contract(
        blocks,
        failed,
        {"min_chars": 2000, "target_chars": 2500, "max_chars": 3000},
        violations=[{"reason_code": "length_out_of_range"}],
    )
    parse = repair_response_parser(blocks, failed, contract)
    first = {
        "replacements": [
            {"block_id": key, "content_text": token * (size - 1) + "。"}
            for key, token, size in (
                ("B02", "庚", 378),
                ("B05", "辛", 455),
                ("B06", "壬", 585),
            )
        ]
    }
    second = {
        "replacements": [
            {"block_id": key, "content_text": token * (size - 1) + "。"}
            for key, token, size in (
                ("B02", "癸", 182),
                ("B05", "子", 247),
                ("B06", "丑", 272),
            )
        ]
    }

    try:
        parse(json.dumps(first, ensure_ascii=False))
    except ValueError:
        pass
    result = parse(json.dumps(second, ensure_ascii=False))
    by_id = {
        item["block_id"]: item["content_text"] for item in result["block_contents"]
    }

    assert result["char_count"] == 2370
    assert by_id["B02"] == "癸" * 181 + "。"
    assert by_id["B05"] == "子" * 246 + "。"
    assert by_id["B06"] == "丑" * 271 + "。"
