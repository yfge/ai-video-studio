from app.services.storyboard.grid_storyboard_prompt_bridge import (
    build_clip_storyboard_sheet_prompt,
    build_clip_storyboard_video_prompt,
)


def test_clip_storyboard_sheet_prompt_includes_bound_context():
    panels = [
        {
            "panel_index": 1,
            "clip_id": "clip-1",
            "visual_prompt": "林晚站在雨夜门口",
            "direction_anchor": "雨夜门口的孤独寻找",
            "bound_context": {
                "characters": [
                    {
                        "name": "林晚",
                        "virtual_ip_id": 7,
                        "anchor_url": "https://cdn.example/linwan.png",
                    }
                ],
                "environment": {
                    "hint": "老城区门廊，冷色雨夜霓虹，门内暖光",
                    "reference_url": "https://cdn.example/rain-door.png",
                },
                "warnings": ["character_context_not_resolved"],
            },
        }
    ]

    prompt = build_clip_storyboard_sheet_prompt(
        panels,
        style="live_action",
    )

    assert "Character anchors:" in prompt
    assert "林晚" in prompt
    assert "Environment anchor: 老城区门廊" in prompt
    assert "Reference image roles:" in prompt
    assert "character_context_not_resolved" in prompt


def test_clip_storyboard_video_prompt_uses_motion_sections():
    panel = {
        "panel_index": 1,
        "clip_id": "clip-1",
        "video_prompt": "穿深色西装的男人坐在车内，雨夜霓虹反射在车窗上",
        "camera_movement": "locked tripod shot",
        "motion_timeline": [
            {"at_ms": 0, "action": "the subject remains still"},
            {"at_ms": 2400, "action": "the subject slowly turns his eyes"},
        ],
    }

    prompt = build_clip_storyboard_video_prompt(panel)

    assert "Use the reference image for identity" in prompt
    assert "Motion timeline:" in prompt
    assert "the subject slowly turns his eyes" in prompt
    assert "dark suit" not in prompt.lower()
    assert "neon" not in prompt.lower()
