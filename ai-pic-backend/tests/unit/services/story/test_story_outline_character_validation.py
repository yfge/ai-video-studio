from __future__ import annotations

from app.services.story.story_outline_character_validation import (
    validate_story_outline_characters,
)


def test_story_outline_character_validation_allows_generic_business_roles() -> None:
    result = validate_story_outline_characters(
        {
            "premise": "AP回归发现数据被篡改，客户当场质疑。",
            "synopsis": (
                "客户: 这份数据不可信。\n"
                "内鬼: 你没有证据。\n"
                "AP回归用手机录音和投屏证据反击，团队成员和竞争对手公司只作为背景压力存在。"
            ),
            "main_characters": [
                {"name": "AP回归-20260618T164912", "description": "项目负责人"},
                {"name": "客户代表", "description": "会议背景压力角色"},
                {"name": "团队成员", "description": "背景人"},
                {"name": "竞争对手公司", "description": "未具名外部压力"},
            ],
        },
        [{"name": "AP回归角色-20260618T164912", "description": "项目负责人"}],
    )

    assert result["character_validation_passed"] is True
    assert result["character_warnings"] == []
