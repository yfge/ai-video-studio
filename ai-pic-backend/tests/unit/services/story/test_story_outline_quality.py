import pytest

from app.services.story.story_outline_quality import validate_story_outline_quality


@pytest.mark.unit
def test_validate_story_outline_quality_uses_outline_fields() -> None:
    story = {
        "premise": "女主推门发现背叛视频正在公司大屏播放。",
        "synopsis": (
            "突然，女主在年会现场发现偷拍视频被公开，危机和冲突立刻爆发。"
            "她顶住压力反查证据，紧张对抗不断升级，中段揭示竞争对手才是真正黑手。"
            "最终高潮对决中真相曝光，女主完成反击并收束结局。"
        ),
        "plot_structure": {
            "act1": "突然爆出羞辱视频，女主被迫当场反击。",
            "act2": "危机升级，双方围绕证据和职位展开紧张对抗。",
            "act3": "高潮揭示真相，女主解决危机完成逆袭结局。",
        },
        "hook_plan": {
            "opening_hook": "突然，女主推门发现背叛视频正在播放。",
            "escalation_plan": "冲突每一场都升级。",
            "payoff_plan": "最终真相揭示并完成反击。",
            "key_reversals": [
                {
                    "beat_type": "hook",
                    "description": "偷拍视频公开",
                    "timing": "开场",
                    "intensity": "high",
                }
            ],
        },
        "cliffhanger_plan": ["但是她发现幕后黑手另有其人"],
    }

    result = validate_story_outline_quality(story)

    assert result["story_quality_passed"] is True
    quality = result["story_quality_result"]
    assert quality["pacing_analysis"]["overall_score"] >= 0.6
    assert quality["hook_score"] >= 0.5


@pytest.mark.unit
def test_validate_story_outline_quality_fails_weak_story() -> None:
    story = {
        "premise": "一个普通的日常生活故事。",
        "synopsis": "大家平静地上班，普通地聊天，最后事情结束。",
        "plot_structure": {
            "act1": "普通开始。",
            "act2": "普通发展。",
            "act3": "平静结束。",
        },
        "hook_plan": {
            "opening_hook": "普通的一天开始了。",
            "key_reversals": [],
        },
    }

    result = validate_story_outline_quality(story)

    assert result["story_quality_passed"] is False
    issue_types = {
        issue["issue_type"] for issue in result["story_quality_result"]["issues"]
    }
    assert "pacing_issue" in issue_types
    assert "weak_hook" in issue_types
