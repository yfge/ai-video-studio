from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest


def _weak_outline() -> dict:
    return {
        "premise": "金融精英兼网络小说家文闻遭遇狗血事件。",
        "synopsis": "文闻上班，林晚出现，阿飞帮助她，最后事情结束。",
        "main_conflict": "文闻遇到一些麻烦。",
        "resolution": "文闻解决问题。",
        "main_characters": [
            {"name": "文闻", "description": "金融白领"},
            {"name": "林晚", "description": "职场对手"},
            {"name": "阿飞", "description": "混混"},
        ],
        "plot_structure": {
            "act1": "普通开始。",
            "act2": "普通发展。",
            "act3": "普通结束。",
        },
        "hook_plan": {"opening_hook": "普通的一天开始了。", "key_reversals": []},
        "selling_points": ["都市故事"],
        "cliffhanger_plan": ["下集继续"],
        "ad_snippets": [
            {
                "duration_seconds": 15,
                "hook": "继续观看",
                "visual_summary": "角色聊天",
                "call_to_action": "继续看",
            }
        ],
    }


def _strong_outline() -> dict:
    return {
        "premise": "文闻在公司年会突然发现背叛视频被公开，必须当场反击。",
        "synopsis": (
            "突然，文闻在年会现场发现偷拍视频被公开，危机和冲突立刻爆发。"
            "她顶住压力反查证据，紧张对抗不断升级，中段揭示林晚_爽剧测试_01300519才是真正黑手。"
            "最终高潮对决中真相曝光，文闻完成反击并收束结局。"
        ),
        "main_conflict": "文闻必须在公开羞辱和职场陷害中找出真相。",
        "resolution": "文闻揭示真相，解决危机并完成逆袭。",
        "main_characters": [
            {"name": "文闻", "description": "金融白领"},
            {"name": "林晚_爽剧测试_01300519", "description": "职场对手"},
            {"name": "阿飞", "description": "混混"},
        ],
        "plot_structure": {
            "act1": "突然爆出羞辱视频，文闻被迫当场反击。",
            "act2": "危机升级，文闻与林晚_爽剧测试_01300519围绕证据紧张对抗。",
            "act3": "高潮揭示真相，文闻解决危机完成逆袭结局。",
        },
        "hook_plan": {
            "opening_hook": "突然，文闻推门发现背叛视频正在播放。",
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
        "selling_points": [
            "开场公开羞辱",
            "高压反击",
            "真相揭示",
            "职场逆袭",
            "强卡点",
        ],
        "cliffhanger_plan": ["但是她发现幕后黑手另有其人"],
        "ad_snippets": [
            {
                "duration_seconds": 15,
                "hook": "背叛视频公开",
                "visual_summary": "年会大屏公开证据",
                "call_to_action": "看她如何反击",
            }
        ],
    }


@pytest.mark.asyncio
async def test_story_agent_repairs_when_outline_fails_quality_or_character_gate():
    from app.services.story_agent import LANGGRAPH_AVAILABLE, StoryLangGraphAgent

    if not LANGGRAPH_AVAILABLE:
        pytest.skip("langgraph not available")

    calls: list[str] = []
    responses = [_weak_outline(), _strong_outline()]

    async def _generate_text(**kwargs: object):
        schema = kwargs.get("json_schema")
        name = schema.get("name") if isinstance(schema, dict) else ""
        calls.append(str(name))
        return SimpleNamespace(
            success=True,
            data=responses[len(calls) - 1],
            provider="deepseek",
            model="deepseek-v4-flash",
            usage={"total_tokens": 1},
        )

    service = SimpleNamespace(ai_manager=SimpleNamespace(generate_text=_generate_text))
    agent = StoryLangGraphAgent(service)

    with patch(
        "app.services.story_agent.prompt_manager.render_prompt", return_value="prompt"
    ):
        result = await agent.generate(
            title="我的生活被狗血包围",
            story_format="short_drama",
            genre="drama",
            characters=[
                {"name": "文闻", "description": "金融白领"},
                {"name": "林晚_爽剧测试_01300519", "description": "职场对手"},
                {"name": "阿飞", "description": "混混"},
            ],
            market_region="KRJP",
            micro_genre="校园逆袭",
            pacing_template="twist-heavy",
            hook_plan={"opening_hook": "开场直接给出冲突结果"},
            twist_density="2+/集",
            cliffhanger_plan=["用未揭开的秘密作为下一集引子"],
            ad_snippets=[],
            theme="狗血",
            target_audience="成人",
            duration_minutes=51,
            setting_time="现代",
            setting_location="北京",
            world_building=None,
            additional_requirements=None,
            style_preferences=[],
            content_restrictions=[],
            model="deepseek-v4-flash",
            prefer_provider="deepseek",
            temperature=0.7,
        )

    assert result is not None
    assert calls == ["story_outline", "story_outline_repair"]
    assert (
        result["normalized"]["main_characters"][1]["name"] == "林晚_爽剧测试_01300519"
    )
    assert result["character_validation_passed"] is True
    assert result["story_quality_passed"] is True
    assert result["reasoning"] == [
        "draft_ok",
        "repair_attempt_1",
        "validated_attempt_1",
    ]
