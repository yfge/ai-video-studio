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


def _story_seed() -> dict:
    return {
        "story_seed": {
            "schema": "story_seed_v1",
            "title": "AP全链路回归样片",
            "premise": "文闻发现项目数据被篡改。",
            "outline": "文闻追查数据篡改，并逐步逼近内部黑手。",
            "protagonists": [
                {
                    "virtual_ip_business_id": "vip-wenwen",
                    "initial_state": "负责项目但尚未掌握证据",
                }
            ],
            "world_constraints": ["关键结论必须有业务记录佐证"],
            "central_conflict": "文闻必须借用被质疑的团队资源反查团队",
            "ending_direction": "查清真相并夺回项目主导权",
            "target_audience": "都市职场逆袭用户",
            "content_constraints": [],
        }
    }


def _production_generate_kwargs() -> dict:
    return {
        "title": "AP全链路回归样片",
        "story_format": "short_drama",
        "genre": "drama",
        "characters": [
            {"business_id": "vip-wenwen", "name": "文闻", "description": "项目负责人"},
            {"business_id": "vip-linwan", "name": "林晚", "description": "职场对手"},
            {"business_id": "vip-afei", "name": "阿飞", "description": "外部压力来源"},
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
async def test_story_agent_repairs_production_output_until_seed_gate_passes():
    from app.prompts.templates import PromptTemplate
    from app.services.story_agent import LANGGRAPH_AVAILABLE, StoryLangGraphAgent

    if not LANGGRAPH_AVAILABLE:
        pytest.skip("langgraph not available")

    calls: list[str] = []
    repair_vars: dict = {}
    responses = [_strong_outline(), _story_seed()]

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
    assert result["normalized"]["story_seed"]["schema"] == "story_seed_v1"
    assert repair_vars["production_mode"] is True
    assert "story_seed" in repair_vars["missing_fields"]


@pytest.mark.asyncio
async def test_story_agent_production_schema_requires_story_seed():
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
            data=_story_seed(),
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

    assert captured_schema["required"] == ["story_seed"]
    seed_schema = captured_schema["$defs"]["StorySeedModel"]
    assert "premise" in seed_schema["required"]
    assert "central_conflict" in seed_schema["required"]
