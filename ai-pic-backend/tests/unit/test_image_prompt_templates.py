from app.prompts.manager import prompt_manager
from app.prompts.template_audit import build_prompt_template_audit


def test_virtual_ip_image_prompt_template_renders():
    prompt = prompt_manager.render_prompt(
        "virtual_ip_image",
        {
            "character_name": "测试角色",
            "character_description": "短发、黑框眼镜，身形清瘦，极客气质",
            "background_story": None,
            "style": "realistic",
            "category": "portrait",
            "style_prompt": None,
            "additional_prompts": ["studio lighting"],
        },
    )

    assert "Virtual IP Character:" in prompt
    assert "Quality:" in prompt
    assert "Constraints:" in prompt
    assert "no watermark" in prompt.lower()
    assert "no collage" in prompt.lower()


def test_virtual_ip_image_variant_prompt_template_renders():
    prompt = prompt_manager.render_prompt(
        "virtual_ip_image_variant",
        {
            "character_name": "测试角色",
            "variant_prompt": "背面照，全身照，保持同一人物特征",
            "character_description": "短发、黑框眼镜，身形清瘦，极客气质",
            "background_story": None,
            "style": "realistic",
            "category": "portrait",
            "style_prompt": None,
            "base_prompt": None,
        },
    )

    assert "Virtual IP Variant:" in prompt
    assert "Variant Instructions:" in prompt
    assert "no watermark" in prompt.lower()


def test_environment_image_prompt_template_renders_constraints():
    prompt = prompt_manager.render_prompt(
        "environment_image",
        {
            "environment_name": "未来科技办公室",
            "category": "indoor",
            "tags": "科幻, 办公室, 未来",
            "description": "悬浮屏幕、玻璃隔断、冷色调灯光",
            "prompt": "冷色调科幻办公室，玻璃隔断与悬浮屏幕",
            "additional_prompts": None,
        },
    )

    assert "Environment:" in prompt
    assert "Constraints:" in prompt
    assert "Quality:" in prompt
    assert "no watermark" in prompt.lower()


def test_environment_image_variant_prompt_template_renders_instructions():
    prompt = prompt_manager.render_prompt(
        "environment_image_variant",
        {
            "environment_name": "未来科技办公室",
            "category": "indoor",
            "tags": "科幻, 办公室, 未来",
            "description": "悬浮屏幕、玻璃隔断、冷色调灯光",
            "base_prompt": "冷色调科幻办公室，玻璃隔断与悬浮屏幕",
            "variant_prompt": "改为夜景，增加玻璃反射与更强对比度灯光",
        },
    )

    assert "Environment Variant:" in prompt
    assert "Variant Instructions:" in prompt
    assert "Constraints:" in prompt
    assert "no watermark" in prompt.lower()
    assert "no collage" in prompt.lower()


def test_storyboard_image_prompt_template_includes_quality_and_constraints():
    prompt = prompt_manager.render_prompt(
        "storyboard_image_prompt",
        {
            "base_prompt": "夜色中的仓库，景别: 中景",
            "style": "realistic",
            "reference_notes": [{"type": "frame"}],
        },
    )

    assert "Quality:" in prompt
    assert "Constraints:" in prompt
    assert "no watermark" in prompt.lower()
    assert "no readable text" in prompt.lower()
    assert "no split-screen" in prompt.lower()
    assert "no multiple faces" not in prompt.lower()
    assert "不得混入其他角色身份" in prompt
    assert "不得把环境参考图中的人物带入" in prompt
    assert "显式风格“realistic”是最高优先级" in prompt


def test_prompt_template_audit_has_version_and_hash():
    audit = build_prompt_template_audit("virtual_ip_image")
    assert audit["resolved_template"] == "virtual_ip_image"
    assert audit["version"]
    assert isinstance(audit["sources_hash"], str)
    assert len(audit["sources_hash"]) == 64
