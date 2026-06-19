from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest


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
        "selling_points": ["开场公开羞辱", "高压反击", "真相揭示", "职场逆袭", "强卡点"],
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


def _strong_outline_with_contract() -> dict:
    outline = _strong_outline()
    outline["structured_story_contract"] = {
        "target_audience": "都市职场逆袭用户",
        "core_emotional_pain": "专业能力被公开质疑，信任被内部人背叛",
        "big_expectation": "文闻查清数据篡改真相并夺回项目主导权",
        "small_expectation_ladder": [
            "前三集拿到会议录音",
            "第8-12集逼出篡改数据的人",
            "第20-30集公开幕后交易证据",
        ],
        "protagonist_goal": "三天内找出篡改数据的内部人",
        "structural_conflict": "文闻必须借用质疑她的团队资源反查团队内部黑手",
        "information_gap": "观众知道录音存在，对手不知道关键镜头已被拍下",
        "first_three_episode_spine": "身份、证据、核心冲突前三集立住",
        "stage_highs": ["会议室反击", "走廊抢手机", "董事会翻盘"],
        "shootability": "会议室、办公室、走廊三类低成本可拍场景",
        "compliance_risks": [],
        "traffic_hooks": ["大屏公开篡改数据", "手机录音反击"],
    }
    return outline


def _production_generate_kwargs() -> dict:
    return {
        "title": "AP全链路回归样片",
        "story_format": "short_drama",
        "genre": "drama",
        "characters": [
            {"name": "文闻", "description": "商业咨询公司项目负责人"},
            {"name": "林晚_爽剧测试_01300519", "description": "职场对手"},
            {"name": "阿飞", "description": "外部压力来源"},
        ],
        "market_region": "CN",
        "micro_genre": "职场逆袭",
        "pacing_template": "twist-heavy",
        "hook_plan": {"opening_hook": "开场直接给出冲突结果"},
        "twist_density": "2+/集",
        "cliffhanger_plan": ["用未揭开的秘密作为下一集引子"],
        "ad_snippets": [],
        "theme": "商业职场",
        "target_audience": "成人",
        "duration_minutes": 3,
        "setting_time": "现代",
        "setting_location": "商业咨询公司",
        "world_building": None,
        "additional_requirements": None,
        "style_preferences": [],
        "content_restrictions": [],
        "model": "deepseek-v4-flash",
        "prefer_provider": "deepseek",
        "temperature": 0.7,
        "generation_mode": "production",
    }


@pytest.mark.asyncio
async def test_story_agent_repairs_production_outline_until_contract_gate_passes():
    from app.prompts.templates import PromptTemplate
    from app.services.story_agent import LANGGRAPH_AVAILABLE, StoryLangGraphAgent

    if not LANGGRAPH_AVAILABLE:
        pytest.skip("langgraph not available")

    calls: list[str] = []
    repair_vars: dict = {}
    responses = [_strong_outline(), _strong_outline_with_contract()]

    async def _generate_text(**kwargs: object):
        schema = kwargs.get("json_schema")
        calls.append(str(schema.get("name") if isinstance(schema, dict) else ""))
        return SimpleNamespace(
            success=True,
            data=responses[len(calls) - 1],
            provider="deepseek",
            model="deepseek-v4-flash",
            usage={"total_tokens": 1},
        )

    def _render_prompt(template_name: str, variables: dict) -> str:
        if template_name == PromptTemplate.STORY_OUTLINE_REPAIR.value:
            repair_vars.update(variables)
            return "repair prompt"
        return "prompt"

    service = SimpleNamespace(ai_manager=SimpleNamespace(generate_text=_generate_text))
    agent = StoryLangGraphAgent(service)

    with patch("app.services.story_agent.prompt_manager.render_prompt", _render_prompt):
        result = await agent.generate(**_production_generate_kwargs())

    assert calls == ["story_outline", "story_outline_repair"]
    assert result["quality_gate"]["passed"] is True
    assert result["normalized"]["structured_story_contract"]["compliance_risks"] == []
    assert repair_vars["production_mode"] is True
    assert "structured_story_contract_required" in repair_vars["quality_gate_issues"]


@pytest.mark.asyncio
async def test_story_agent_production_schema_requires_structured_contract():
    from app.services.story_agent import LANGGRAPH_AVAILABLE, StoryLangGraphAgent

    if not LANGGRAPH_AVAILABLE:
        pytest.skip("langgraph not available")

    captured_schema: dict = {}

    async def _generate_text(**kwargs: object):
        schema = kwargs.get("json_schema")
        if isinstance(schema, dict):
            captured_schema.update(schema.get("schema") or {})
        return SimpleNamespace(
            success=True,
            data=_strong_outline_with_contract(),
            provider="deepseek",
            model="deepseek-v4-flash",
            usage={"total_tokens": 1},
        )

    service = SimpleNamespace(ai_manager=SimpleNamespace(generate_text=_generate_text))
    agent = StoryLangGraphAgent(service)

    with patch(
        "app.services.story_agent.prompt_manager.render_prompt", return_value="prompt"
    ):
        await agent.generate(**_production_generate_kwargs())

    assert "structured_story_contract" in captured_schema["required"]
    contract_schema = captured_schema["properties"]["structured_story_contract"]
    assert "target_audience" in contract_schema["required"]
    assert "traffic_hooks" in contract_schema["required"]
