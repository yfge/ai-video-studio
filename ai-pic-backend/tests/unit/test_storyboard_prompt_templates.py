from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate


def test_storyboard_image_prompt_template_forbids_collage():
    base_prompt = "老拐, 执行最终压力测试，负载提升至峰值。 景别: 中景 运镜: 固定 构图: 三分法 镜头切换: 开场"

    prompt = prompt_manager.render_prompt(
        PromptTemplate.STORYBOARD_IMAGE_PROMPT.value,
        {"base_prompt": base_prompt, "reference_notes": []},
    )

    assert base_prompt in prompt
    assert "只生成单幅画面" in prompt
    assert "不要拼接" in prompt
    assert "no collage" in prompt.lower()


def test_storyboard_image_fallback_template_forbids_collage():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.STORYBOARD_IMAGE_FALLBACK.value,
        {"frame_index": 1, "scene_number": 2},
    )

    assert "只生成单幅画面" in prompt
    assert "不要拼接" in prompt


def test_storyboard_grid_sheet_template_allows_sheet_but_limits_text():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.STORYBOARD_GRID_SHEET.value,
        {
            "layout_label": "3x3",
            "panel_count": 9,
            "style": "vertical short-drama, cinematic realism",
            "panel_briefs": [
                "Panel 1 / clip clip-1: 林晚站在雨夜门口，霓虹反光，中景",
                "Panel 2 / clip clip-2: 陈哲坐在车内，侧脸被手机屏照亮",
            ],
        },
    )

    assert "3x3" in prompt
    assert "9-panel" in prompt
    assert "storyboard sheet" in prompt.lower()
    assert "panel numbers" in prompt
    assert "shot labels" in prompt
    assert "outside the cinematic panels" in prompt
    assert "No subtitles" in prompt
    assert "林晚站在雨夜门口" in prompt


def test_storyboard_grid_video_template_scopes_to_one_panel():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.STORYBOARD_GRID_VIDEO.value,
        {
            "panel_index": 2,
            "clip_id": "clip-2",
            "video_prompt": "镜头保持静止，只捕捉他的犹豫表情",
        },
    )

    assert "Use panel 2 only" in prompt
    assert "clip-2" in prompt
    assert "Generate only this shot" in prompt
    assert "other panels" in prompt
    assert "镜头保持静止" in prompt


def test_storyboard_keyframe_template_forbids_collage():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.STORYBOARD_KEYFRAME.value,
        {"base_prompt": "夜色中的办公室，景别: 中景", "role": "start"},
    )

    assert "只生成单幅画面" in prompt
    assert "剪辑备注" in prompt
    assert "首帧" in prompt


def test_storyboard_scene_template_forbids_on_screen_text():
    prompt = prompt_manager.render_prompt(
        "storyboard_scene",
        {
            "scene_plan_json": '{"scene_number": 1, "target_frames": 3, "frames": []}',
            "script_brief_json": '{"story": {"title": "测试"}, "scenes": []}',
            "max_frames": None,
        },
    )

    assert "不要包含任何“画面中出现的文字内容”" in prompt
    assert "无可读文字" in prompt


def test_storyboard_audio_visual_prompt_templates_exist():
    prompt = prompt_manager.render_prompt(
        "storyboard_audio_visual_dialogue_spoken",
        {"speaker": "林晚", "intent": "质问/指控"},
    )
    assert "林晚" in prompt
    assert "无字幕" in prompt

    prompt = prompt_manager.render_prompt(
        "storyboard_audio_visual_dialogue_voiceover",
        {"speaker": "林晚", "intent": None},
    )
    assert "林晚" in prompt
    assert "旁白" in prompt or "内心独白" in prompt

    prompt = prompt_manager.render_prompt(
        "storyboard_audio_visual_dialogue_read_text",
        {"speaker": "林晚"},
    )
    assert "屏幕文字模糊不可读" in prompt
    assert "无字幕" in prompt

    prompt = prompt_manager.render_prompt(
        "storyboard_audio_visual_action",
        {"action": "她猛地把文件拍在桌上，怒视对方"},
    )
    assert "拍在桌上" in prompt
    assert "无字幕" in prompt

    prompt = prompt_manager.render_prompt("storyboard_audio_visual_pause", {})
    assert "停顿" in prompt
    assert "无字幕" in prompt

    prompt = prompt_manager.render_prompt(
        "storyboard_audio_visual_context",
        {
            "base": "林晚开口说话，嘴型清晰。",
            "character_cards": ["林晚: 黑长发，米色毛衣", "陈哲: 短发，深色夹克"],
            "environment": "公寓客厅，夜",
        },
    )
    assert "角色卡" in prompt
    assert "环境锚点" in prompt
