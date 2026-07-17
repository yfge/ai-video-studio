from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate


def test_story_outline_template_resolves_tv_series_variant():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.STORY_OUTLINE.value,
        {
            "title": "测试故事",
            "story_format": "tv_series",
            "genre": "剧情",
            "characters": [{"name": "主角", "description": "测试"}],
            "market_region": None,
            "micro_genre": None,
            "theme": None,
            "target_audience": None,
            "duration_minutes": 60,
            "setting_time": None,
            "setting_location": None,
            "world_building": None,
            "additional_requirements": None,
            "style_preferences": [],
            "content_restrictions": [],
        },
    )

    assert "电视剧/网剧" in prompt


def test_story_outline_template_resolves_film_variant():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.STORY_OUTLINE.value,
        {
            "title": "测试电影",
            "story_format": "film",
            "genre": "剧情",
            "characters": [{"name": "主角", "description": "测试"}],
            "market_region": None,
            "micro_genre": None,
            "theme": None,
            "target_audience": None,
            "duration_minutes": 120,
            "setting_time": None,
            "setting_location": None,
            "world_building": None,
            "additional_requirements": None,
            "style_preferences": [],
            "content_restrictions": [],
        },
    )

    assert "电影编剧" in prompt


def test_story_outline_template_resolves_short_drama_variant():
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
        },
    )

    assert "【短剧硬性要求】每集必有爽点" in prompt


def test_system_prompt_story_resolves_film_variant():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.SYSTEM_PROMPT_STORY.value, {"story_format": "film"}
    )

    assert "电影编剧" in prompt


def test_episode_generation_template_resolves_tv_series_variant():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.EPISODE_GENERATION.value,
        {
            "story": {
                "title": "测试故事",
                "genre": "剧情",
                "story_format": "tv_series",
            },
            "episode_count": 3,
            "episode_duration": 45,
            "focus_characters": [],
            "plot_complexity": "medium",
            "pacing": "medium",
            "additional_requirements": None,
            "style_preferences": [],
        },
    )

    assert "电视剧/网剧" in prompt


def test_episode_generation_template_resolves_short_drama_variant():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.EPISODE_GENERATION.value,
        {
            "story": {
                "title": "测试短剧",
                "genre": "剧情",
                "story_format": "short_drama",
            },
            "episode_count": 5,
            "episode_duration": 3,
            "focus_characters": [],
            "plot_complexity": "medium",
            "pacing": "fast",
            "additional_requirements": None,
            "style_preferences": [],
        },
    )

    assert "【短剧硬性规则】每集必有爽点" in prompt


def test_script_generation_template_resolves_short_drama_variant():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.SCRIPT_GENERATION.value,
        {
            "story": {
                "title": "测试短剧",
                "genre": "剧情",
                "story_format": "short_drama",
            },
            "episode": {"episode_number": 1, "title": "第一集", "duration_minutes": 3},
            "format_type": "teleplay",
            "language": "zh-CN",
            "dialogue_style": "dramatic",
            "scene_detail_level": "medium",
            "additional_requirements": None,
            "style_preferences": [],
        },
    )

    assert "PAYOFF" in prompt
    assert "CLIFFHANGER" in prompt


def test_episode_from_outline_template_resolves_short_drama_variant():
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
        },
    )

    assert "【短剧硬性规则】每集必有爽点" in prompt


def test_episode_duration_reject_template_resolves_short_drama_variant():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.EPISODE_DURATION_REJECT.value,
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
            "rejected_episode": {
                "episode_number": 1,
                "title": "第一集",
                "summary": "测试概要",
                "scenes": [
                    {
                        "scene_number": 1,
                        "summary": "测试场景",
                        "estimated_duration_seconds": 30,
                    }
                ],
            },
            "target_duration_seconds": 180,
            "current_duration_seconds": 150,
            "rejection_reason": "duration_too_short",
            "attempt_number": 2,
            "focus_characters": [],
            "episode_duration": 3,
            "plot_complexity": "medium",
            "pacing": "fast",
        },
    )

    assert "【短剧硬性规则】每集必有爽点" in prompt


def test_script_scenes_template_resolves_film_variant():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.SCRIPT_SCENES.value,
        {
            "story": {"title": "测试电影", "genre": "剧情", "story_format": "film"},
            "episode": {"episode_number": 1, "title": "第一幕"},
            "scene_detail_level": "medium",
            "format_type": "screenplay",
            "language": "zh-CN",
            "style_preferences": [],
            "additional_requirements": "",
            "duration_minutes": 120,
            "min_scene_seconds": 10,
            "max_scene_seconds": 120,
        },
    )

    assert "电影模式" in prompt


def test_script_scenes_short_drama_production_prompt_has_quality_brief():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.SCRIPT_SCENES.value,
        {
            "story": {
                "title": "测试短剧",
                "genre": "剧情",
                "story_format": "short_drama",
            },
            "episode": {"episode_number": 1, "title": "第一集"},
            "scene_detail_level": "medium",
            "format_type": "screenplay",
            "language": "zh-CN",
            "style_preferences": [],
            "additional_requirements": "",
            "duration_minutes": 3,
            "min_scene_seconds": 10,
            "max_scene_seconds": 120,
            "generation_mode": "production",
            "production_mode": True,
            "script_score_thresholds": {"overall": 4.5, "dimension": 4.2},
        },
    )
    assert "生产级场景规划硬门槛" in prompt
    assert "timestamp skeleton" in prompt
    assert "0-3 秒 ignition" in prompt
    assert "close-up reaction" in prompt
    assert "不得用其他题材样板替换" in prompt
    assert "只能来自当前 story / episode / additional_requirements" in prompt
    assert "不要只写“情绪升级/剧情推进”" in prompt
    assert "问题 -> 行动 -> 结果变化" in prompt


def test_script_scenes_short_drama_standard_prompt_omits_production_brief():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.SCRIPT_SCENES.value,
        {
            "story": {
                "title": "测试短剧",
                "genre": "剧情",
                "story_format": "short_drama",
            },
            "episode": {"episode_number": 1, "title": "第一集"},
            "scene_detail_level": "medium",
            "format_type": "screenplay",
            "language": "zh-CN",
            "style_preferences": [],
            "additional_requirements": "",
            "duration_minutes": 3,
            "min_scene_seconds": 10,
            "max_scene_seconds": 120,
            "generation_mode": "standard",
            "production_mode": False,
            "script_score_thresholds": {"overall": 4.5, "dimension": 4.2},
        },
    )

    assert "生产级场景规划硬门槛" not in prompt
    assert "timestamp skeleton" not in prompt
