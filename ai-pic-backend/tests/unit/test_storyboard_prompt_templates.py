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
