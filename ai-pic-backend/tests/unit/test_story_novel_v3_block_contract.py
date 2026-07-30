import json

import anyio
import pytest
from app.services.story.story_novel_block_contract import (
    assemble_prose_blocks,
    parse_prose_blocks,
    recover_complete_prose_blocks,
    recover_unescaped_prose_blocks,
    repair_block_context,
    replace_prose_blocks,
)
from app.services.story.story_novel_export_ai import TruncatedNovelOutput
from app.services.story.story_novel_invocation_evidence import GeneratedNovelText
from app.services.story.story_novel_v3_generation import (
    generate_prose_blocks,
    repair_blocks,
)
from app.services.story.story_novel_v3_repair_length import replacement_length_contract


def _blocks():
    return [
        {"block_id": "B01", "content_text": "第一块，保留空格 A。"},
        {"block_id": "B02", "content_text": "第二块需要返修。"},
        {"block_id": "B03", "content_text": "第三块字节不变。"},
    ]


def test_blocks_parse_and_assemble_with_stable_offsets_and_hashes():
    blocks = parse_prose_blocks({"blocks": _blocks()}, expected_count=3)
    assembled = assemble_prose_blocks(blocks)

    assert assembled["content_text"] == (
        "第一块，保留空格 A。\n\n第二块需要返修。\n\n第三块字节不变。"
    )
    for item, source in zip(assembled["blocks"], blocks):
        assert (
            assembled["content_text"][item["start"] : item["end"]]
            == source["content_text"]
        )
        assert item["content_hash"]
    assert assembled["source_hash"]


def test_local_replacement_preserves_all_other_block_bytes():
    before = _blocks()
    replaced = replace_prose_blocks(before, {"B02": "第二块已局部修复。"})

    assert replaced[0]["content_text"].encode() == before[0]["content_text"].encode()
    assert replaced[1]["content_text"] == "第二块已局部修复。"
    assert replaced[2]["content_text"].encode() == before[2]["content_text"].encode()


def test_local_repair_context_includes_adjacent_blocks_as_read_only():
    context = repair_block_context(_blocks(), {"B02"})

    assert [item["block_id"] for item in context] == ["B01", "B02", "B03"]
    assert [item["editable"] for item in context] == [False, True, False]


def test_repair_length_counts_read_only_blocks_without_renumbering_them():
    blocks = [
        {"block_id": "B01", "content_text": "甲" * 1000},
        {"block_id": "B02", "content_text": "乙" * 400},
        {"block_id": "B03", "content_text": "丙" * 980},
    ]

    contract = replacement_length_contract(
        blocks,
        {"B02"},
        {"min_chars": 2000, "target_chars": 2500, "max_chars": 3000},
    )

    assert contract["fixed_chars"] == 1980
    assert contract["replacement_min_chars"] == 20
    assert contract["replacement_target_chars"] == 520
    assert contract["replacement_max_chars"] == 1020


def test_blocks_fail_closed_on_extra_fields_gaps_and_unknown_replacements():
    with pytest.raises(ValueError, match="只能包含"):
        parse_prose_blocks({"blocks": _blocks(), "plot_delta": {}})
    invalid = _blocks()
    invalid[1]["block_id"] = "B09"
    with pytest.raises(ValueError, match="连续编号"):
        parse_prose_blocks({"blocks": invalid})
    with pytest.raises(ValueError, match="未知 block"):
        replace_prose_blocks(_blocks(), {"B04": "越界"})


def test_blocks_recover_unescaped_dialogue_quotes_only():
    raw = (
        '{"blocks":['
        '{"block_id":"B01","content_text":"沈禾说："先签契。""},'
        '{"block_id":"B02","content_text":"刘岩答道："依约办。""}'
        "]}"
    )

    blocks = recover_unescaped_prose_blocks(raw, expected_count=2)

    assert blocks == [
        {"block_id": "B01", "content_text": '沈禾说："先签契。"'},
        {"block_id": "B02", "content_text": '刘岩答道："依约办。"'},
    ]


def test_blocks_do_not_recover_extra_envelope_fields():
    raw = (
        '{"blocks":[{"block_id":"B01","content_text":"正文"}],'
        '"summary":"not allowed"}'
    )

    with pytest.raises(ValueError, match="结构不完整"):
        recover_unescaped_prose_blocks(raw, expected_count=1)


def test_unparseable_prose_is_bounded_to_one_recovery_call():
    calls = []

    async def generate(_revision, _prompt, *, stage, **_kwargs):
        calls.append(stage)
        return "not-json"

    async def run():
        return await generate_prose_blocks(
            object(),
            3,
            {"chapter_length": {"target_chars": 4000}},
            8,
            generate,
        )

    with pytest.raises(ValueError, match="正文响应只能包含 blocks"):
        anyio.run(run)
    assert calls == ["prose.3", "prose.3.format_repair"]


def test_complete_blocks_are_recovered_from_truncated_json():
    raw = (
        '{"blocks":[{"block_id":"B01","content_text":"第一块"},'
        '{"block_id":"B02","content_text":"第二块"},'
        '{"block_id":"B03","content_text":"未完成'
    )

    assert recover_complete_prose_blocks(raw) == [
        {"block_id": "B01", "content_text": "第一块"},
        {"block_id": "B02", "content_text": "第二块"},
    ]


def test_truncated_prose_continues_only_missing_blocks():
    calls = []
    partial = (
        '{"blocks":[{"block_id":"B01","content_text":"第一块"},'
        '{"block_id":"B02","content_text":"第二块"},'
        '{"block_id":"B03","content_text":"未完成'
    )

    async def generate(_revision, prompt, *, stage, **_kwargs):
        calls.append((stage, prompt))
        if stage == "prose.2":
            raise TruncatedNovelOutput(
                "length", partial, {"invocation_id": 10, "output_tokens": 16000}
            )
        return GeneratedNovelText(
            '{"blocks":[{"block_id":"B03","content_text":"第三块"}]}',
            {"invocation_id": 11, "output_tokens": 300},
        )

    async def run():
        return await generate_prose_blocks(
            object(),
            2,
            {
                "chapter_length": {"target_chars": 4000},
                "chapter_brief": {"beats": []},
            },
            3,
            generate,
        )

    prose, metrics = anyio.run(run)

    assert prose["content_text"] == "第一块\n\n第二块\n\n第三块"
    assert [item[0] for item in calls] == [
        "prose.2",
        "prose.2.truncation_continue",
    ]
    assert "只输出缺失 block_ids=['B03']" in calls[1][1]
    assert metrics["invocation_ids"] == [10, 11]


def test_content_filtered_prose_never_enters_truncation_recovery():
    calls = []

    async def generate(_revision, _prompt, *, stage, **_kwargs):
        calls.append(stage)
        raise TruncatedNovelOutput(
            "content_filter",
            '{"blocks":[{"block_id":"B01","content_text":"过滤内容"}]}',
            {"invocation_id": 12, "product_status": "rejected"},
        )

    async def run():
        return await generate_prose_blocks(
            object(),
            4,
            {
                "chapter_length": {"target_chars": 2500},
                "chapter_brief": {"beats": []},
            },
            1,
            generate,
        )

    with pytest.raises(TruncatedNovelOutput) as exc:
        anyio.run(run)

    assert exc.value.finish_reason == "content_filter"
    assert calls == ["prose.4"]


def test_local_repair_format_retry_enforces_merged_chapter_length():
    calls = []
    blocks = [
        {"block_id": "B01", "content_text": "甲" * 999 + "。"},
        {"block_id": "B02", "content_text": "乙" * 800},
    ]

    async def generate(_revision, prompt, *, stage, **_kwargs):
        calls.append((stage, prompt))
        size = 2100 if stage == "local_repair.8" else 1500
        return GeneratedNovelText(
            json.dumps(
                {
                    "replacements": [
                        {
                            "block_id": "B02",
                            "content_text": "修" * (size - 1) + "。",
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            {"invocation_id": len(calls), "output_tokens": size},
        )

    async def run():
        return await repair_blocks(
            object(),
            8,
            blocks=blocks,
            failed_block_ids=["B02"],
            violations=[],
            prose_input={
                "chapter_brief": {"beats": []},
                "visible_canon": {},
                "chapter_length": {
                    "min_chars": 2000,
                    "target_chars": 2500,
                    "max_chars": 3000,
                },
            },
            generate_text=generate,
        )

    prose, metrics = anyio.run(run)

    assert prose["char_count"] == 2500
    assert [item[0] for item in calls] == [
        "local_repair.8",
        "local_repair.8.format_repair",
    ]
    assert '"replacement_max_chars":2000' in calls[0][1]
    assert metrics["calls"] == 2
