from app.services.story.story_novel_brief_policy import (
    BRIEF_POLICY_VERSION,
    LEGACY_BRIEF_POLICY_VERSION,
    expected_beat_count,
)
from app.services.story.story_novel_continuity_contract import continuity_prompt
from app.services.story.story_novel_length_contract import list_length_profiles


def test_new_commercial_profile_targets_two_to_three_thousand_chars():
    profile = list_length_profiles()[0]

    assert profile == {
        "profile_id": "commercial_serial",
        "name": "商业网文短章",
        "count_mode": "non_whitespace_chars",
        "min_chars": 2000,
        "target_chars": 2500,
        "max_chars": 3000,
    }


def test_legacy_brief_density_remains_available_for_frozen_revisions():
    assert BRIEF_POLICY_VERSION.endswith(".v4")
    assert expected_beat_count(2500, BRIEF_POLICY_VERSION) == 6
    assert expected_beat_count(2500, LEGACY_BRIEF_POLICY_VERSION) == 6


def test_six_chapter_review_treats_reader_engagement_as_non_blocking():
    prompt = continuity_prompt("这是相邻章节全文窗口检查。", {}, issue_limit=12)

    assert "明确为连载或商业网文" in prompt
    assert "每 2–3 章出现一次" in prompt
    assert "只可标" in prompt and "warning" in prompt


def test_global_review_scores_soft_growth_without_per_chapter_kpis():
    prompt = continuity_prompt(
        "这是全书综合检查。", {}, issue_limit=20, include_editorial=True
    )

    assert "认知、能力、资源、活动/时间尺度" in prompt
    assert "某一曲线不适用不扣分" in prompt
    assert "失败、蓄势和有代价的回撤不算停滞" in prompt
    assert "不得把它变成逐章升级 KPI" in prompt
    assert "reader_appeal" in prompt
