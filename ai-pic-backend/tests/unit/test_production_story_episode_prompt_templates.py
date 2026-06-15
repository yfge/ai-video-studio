from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate


def test_story_outline_short_drama_production_prompt_has_researched_brief():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.STORY_OUTLINE.value,
        {
            "title": "测试短剧",
            "story_format": "short_drama",
            "genre": "剧情",
            "characters": [{"name": "主角", "description": "测试"}],
            "market_region": "东南亚",
            "micro_genre": "霸总复仇",
            "theme": None,
            "target_audience": None,
            "duration_minutes": 60,
            "setting_time": None,
            "setting_location": None,
            "world_building": None,
            "additional_requirements": None,
            "style_preferences": [],
            "content_restrictions": [],
            "generation_mode": "production",
            "production_mode": True,
            "story_contract_version": "story_contract_v1",
        },
    )

    assert "structured_story_contract" in prompt
    assert "大期待" in prompt
    assert "小期待阶梯" in prompt
    assert "信息差设计" in prompt
    assert "前三集立主线" in prompt
    assert "少写心理，多写行为" in prompt
    assert "禁止只写“情绪升级、推进剧情、巨大反转”" in prompt


def test_story_outline_short_drama_standard_prompt_omits_production_contract():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.STORY_OUTLINE.value,
        {
            "title": "测试短剧",
            "story_format": "short_drama",
            "genre": "剧情",
            "characters": [{"name": "主角", "description": "测试"}],
            "market_region": "东南亚",
            "micro_genre": "霸总复仇",
            "theme": None,
            "target_audience": None,
            "duration_minutes": 60,
            "setting_time": None,
            "setting_location": None,
            "world_building": None,
            "additional_requirements": None,
            "style_preferences": [],
            "content_restrictions": [],
            "generation_mode": "standard",
            "production_mode": False,
            "story_contract_version": "story_contract_v1",
        },
    )

    assert "structured_story_contract" not in prompt
    assert "前三集立主线" not in prompt


def test_episode_step_outline_production_prompt_requires_contract_and_beats():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.EPISODE_STEP_OUTLINE.value,
        {
            "story": {
                "title": "测试短剧",
                "genre": "剧情",
                "story_format": "short_drama",
            },
            "episode_count": 3,
            "episode_duration": 3,
            "focus_characters": [],
            "plot_complexity": "medium",
            "pacing": "fast",
            "additional_requirements": None,
            "style_preferences": [],
            "generation_mode": "production",
            "production_mode": True,
            "episode_contract_version": "episode_contract_v1",
        },
    )

    assert "structured_episode_contract" in prompt
    assert "production 不接受 logline-only" in prompt
    assert "0-3 秒 ignition" in prompt
    assert "前 30 秒停留理由" in prompt
    assert "episode_goal" in prompt
    assert "next_tap_reason" in prompt


def test_episode_generation_production_prompt_has_dialogue_and_closeup_contract():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.EPISODE_GENERATION.value,
        {
            "story": {
                "title": "测试短剧",
                "genre": "剧情",
                "story_format": "short_drama",
            },
            "episode_count": 3,
            "episode_duration": 3,
            "focus_characters": [],
            "plot_complexity": "medium",
            "pacing": "fast",
            "additional_requirements": None,
            "style_preferences": [],
            "generation_mode": "production",
            "production_mode": True,
            "episode_contract_version": "episode_contract_v1",
        },
    )

    assert "structured_episode_contract" in prompt
    assert "0-3 秒 ignition" in prompt
    assert "dialogue_function" in prompt
    assert "reveal/threat/decision/counterattack/payoff" in prompt
    assert "9:16 close-up" in prompt
    assert "不能末尾硬塞新危机" in prompt


def test_episode_from_outline_production_prompt_has_visual_action_contract():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.EPISODE_FROM_OUTLINE.value,
        {
            "story": {
                "title": "测试短剧",
                "genre": "剧情",
                "story_format": "short_drama",
            },
            "outline": {
                "episode_number": 1,
                "title": "第一集",
                "logline": "测试logline",
            },
            "previous_episodes": [],
            "episode_duration": 3,
            "plot_complexity": "medium",
            "pacing": "fast",
            "additional_requirements": None,
            "style_preferences": [],
            "generation_mode": "production",
            "production_mode": True,
            "episode_contract_version": "episode_contract_v1",
        },
    )

    assert "structured_episode_contract" in prompt
    assert "visual_anchor" in prompt
    assert "信息变化" in prompt
    assert "dialogue_function" in prompt
    assert "final button/cliffhanger" in prompt
