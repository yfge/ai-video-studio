from app.prompts.manager import prompt_manager
from app.services.story.story_novel_export_continuity import (
    ensure_markers,
    extract_chapter_markers,
    normalize_ledger_update_payload,
)


def test_extract_chapter_markers_parses_summary_and_cliffhanger():
    text = (
        "正文第一段\n正文第二段\n\n"
        "【本章小结】\n- 发生了 A\n- 发生了 B\n\n"
        "【本章卡点】\n门外的脚步声越来越近。"
    )
    body, summary, cliffhanger = extract_chapter_markers(text)

    assert body == "正文第一段\n正文第二段"
    assert "- 发生了 A" in summary
    assert "脚步声" in cliffhanger


def test_extract_chapter_markers_strips_leading_marker_block():
    text = (
        "【本章小结】\n- 先给小结\n\n"
        "【本章卡点】\n先给卡点\n\n"
        "正文从这里开始\n继续正文"
    )
    body, summary, cliffhanger = extract_chapter_markers(text)

    assert body.startswith("正文从这里开始")
    assert "先给小结" in summary
    assert cliffhanger == "先给卡点"


def test_ensure_markers_appends_missing_markers():
    body = "正文"
    merged = ensure_markers(
        body, summary_text="- 要点 1\n- 要点 2", cliffhanger_text="钩子句子"
    )

    assert "【本章小结】" in merged
    assert "【本章卡点】" in merged
    assert merged.endswith("\n")


def test_normalize_ledger_update_payload_formats_summary_and_skips_missing_ledger():
    payload = {
        "chapter_summary": ["1. 第一件事", "- 第二件事", "  • 第三件事  "],
        "chapter_cliffhanger": "  钩子  ",
    }
    ledger, summary_text, cliffhanger = normalize_ledger_update_payload(payload)

    assert ledger == {}
    assert summary_text == "- 第一件事\n- 第二件事\n- 第三件事"
    assert cliffhanger == "钩子"


def test_normalize_ledger_update_payload_compacts_ledger_when_present():
    payload = {
        "ledger": {
            "version": 2,
            "facts": list(range(40)),
            "timeline": [{"chapter": 1, "events": ["a"]}] * 50,
            "characters": {"A": {"status": "ok", "goal": "", "relationships": {}}},
            "open_threads": ["x"] * 40,
            "resolved_threads": ["y"] * 40,
        },
        "chapter_summary": "发生了事",
        "chapter_cliffhanger": "",
    }
    ledger, summary_text, cliffhanger = normalize_ledger_update_payload(payload)

    assert ledger["version"] == 2
    assert len(ledger["facts"]) == 25
    assert len(ledger["timeline"]) == 30
    assert len(ledger["open_threads"]) == 25
    assert len(ledger["resolved_threads"]) == 25
    assert summary_text.startswith("- ")
    assert cliffhanger == ""


def test_story_novel_zhihu_prompts_render_with_new_variables():
    base_payload = {
        "story": {"title": "测试故事", "genre": "剧情"},
        "plan": {"chapter_total": 3, "current_chapter": {"chapter_number": 1}},
        "ledger": {
            "version": 1,
            "facts": [],
            "timeline": [],
            "characters": {},
            "open_threads": [],
            "resolved_threads": [],
        },
        "previous_tail": "",
        "chapter": {
            "chapter_number": 1,
            "title": "更新 1",
            "target_words": 1200,
            "key_beats": ["起笔", "推进", "反转"],
            "cliffhanger_hint": "卡点提示",
        },
        "running_summary": "",
        "remaining_target_words": 20000,
        "total_target_words": 20000,
    }

    prompt_manager.render_prompt("story_novel_zhihu_chapter", base_payload)
    prompt_manager.render_prompt(
        "story_novel_zhihu_chapter_rewrite", {**base_payload, "draft": "草稿内容"}
    )

    prompt_manager.render_prompt(
        "story_novel_zhihu_ledger_update",
        {
            "previous_ledger": base_payload["ledger"],
            "chapter_number": 1,
            "chapter_title": "更新 1",
            "chapter_text": "正文\n【本章小结】\n- 要点\n【本章卡点】\n钩子\n",
            "extracted_summary": "- 要点",
            "extracted_cliffhanger": "钩子",
        },
    )
