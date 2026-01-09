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


def test_system_prompt_story_resolves_film_variant():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.SYSTEM_PROMPT_STORY.value, {"story_format": "film"}
    )

    assert "电影编剧" in prompt


def test_episode_generation_template_resolves_tv_series_variant():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.EPISODE_GENERATION.value,
        {
            "story": {"title": "测试故事", "genre": "剧情", "story_format": "tv_series"},
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

