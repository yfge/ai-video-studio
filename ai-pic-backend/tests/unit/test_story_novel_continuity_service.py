from app.services.story.story_novel_continuity_service import (
    GLOBAL_REVIEW_MAX_TOKENS,
    _normalize_report,
    _prompt,
)


def test_global_continuity_review_is_not_limited_to_8192_tokens():
    prompt = _prompt("全局检查。", {"chapters": []}, issue_limit=40)

    assert GLOBAL_REVIEW_MAX_TOKENS == 16_000
    assert "issues 最多 40 条" in prompt
    assert "各不超过 160 个中文字符" in prompt


def test_continuity_issue_ids_are_namespaced_per_review_window():
    report = _normalize_report(
        '{"summary":"x","issues":[{"id":"issue-001","message":"m"}]}',
        "window-3",
    )

    assert report["issues"][0]["id"] == "window-3-issue-001"
