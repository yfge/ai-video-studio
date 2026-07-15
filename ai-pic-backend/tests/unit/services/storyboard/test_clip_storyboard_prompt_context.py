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
                        "card_brief": "林晚: 30岁女性；黑色齐肩发；深色风衣",
                        "appearance_brief": "林晚: 30岁女性，黑色齐肩发，深色风衣",
                        "anchor_url": "https://cdn.example/linwan.png",
                    }
                ],
                "environment": {
                    "hint": "老城区门廊，冷色雨夜霓虹，门内暖光",
                    "reference_url": "https://cdn.example/rain-door.png",
                },
                "reference_bindings": [
                    {
                        "index": 1,
                        "role": "character_identity",
                        "label": "林晚",
                        "source": "canonical_virtual_ip",
                        "url": "https://cdn.example/linwan.png",
                    },
                    {
                        "index": 2,
                        "role": "environment",
                        "label": "scene environment",
                        "source": "scene_environment",
                        "url": "https://cdn.example/rain-door.png",
                    },
                ],
                "warnings": ["character_context_not_resolved"],
            },
        }
    ]

    prompt = build_clip_storyboard_sheet_prompt(
        panels,
        style="live_action",
    )

    assert "Authoritative cast contract:" in prompt
    assert "林晚: 30岁女性，黑色齐肩发，深色风衣" in prompt
    assert "Environment anchor: 老城区门廊" in prompt
    assert "Reference image 1 = 林晚 identity anchor" in prompt
    assert "Reference image 2 = scene environment" in prompt
    assert "character_context_not_resolved" not in prompt


def test_live_action_clip_storyboard_prompt_overrides_stale_cartoon_and_cast_text():
    panels = [
        {
            "panel_index": 1,
            "clip_id": "clip-1",
            "visual_prompt": "A middle-aged man faces a younger man in the living room",
            "aesthetic_reference": "Pixar-style 3D cartoon animation",
            "bound_context": {
                "characters": [
                    {
                        "name": "老拐",
                        "virtual_ip_id": 1,
                        "card_brief": "老拐: 50岁中国男性；短灰发；深色夹克",
                        "appearance_brief": "老拐: 50岁中国男性，短灰发，深色夹克",
                        "anchor_url": "https://cdn.example/laoguai.png",
                    },
                    {
                        "name": "阿盖儿",
                        "virtual_ip_id": 15,
                        "card_brief": "阿盖儿: 28岁中国女性；长黑发；浅色针织衫",
                        "appearance_brief": "阿盖儿: 28岁中国女性，长黑发，浅色针织衫",
                        "anchor_url": "https://cdn.example/agaier.png",
                    },
                ],
                "reference_bindings": [
                    {
                        "index": 1,
                        "role": "character_identity",
                        "label": "老拐",
                        "source": "canonical_virtual_ip",
                        "url": "https://cdn.example/laoguai.png",
                    },
                    {
                        "index": 2,
                        "role": "character_identity",
                        "label": "阿盖儿",
                        "source": "canonical_virtual_ip",
                        "url": "https://cdn.example/agaier.png",
                    },
                ],
                "warnings": [],
            },
        }
    ]

    prompt = build_clip_storyboard_sheet_prompt(panels, style="live_action")

    assert "Authoritative visual style: photorealistic live action" in prompt
    assert "bound cast contract overrides" in prompt
    assert "person count, gender, age, face, hair, wardrobe" in prompt
    assert "Pixar" not in prompt
    assert "3D cartoon" not in prompt
    assert "老拐" in prompt
    assert "阿盖儿" in prompt


def test_3d_cartoon_prompt_keeps_photo_references_identity_only():
    panels = [
        {
            "panel_index": 1,
            "clip_id": "clip-1",
            "visual_prompt": "老拐把手机递给阿盖儿",
            "bound_context": {
                "characters": [
                    {
                        "name": "老拐",
                        "appearance_brief": "老拐: 清瘦，短黑发，深色夹克",
                    },
                    {
                        "name": "阿盖儿",
                        "appearance_brief": "阿盖儿: 少女，长棕发，浅色连衣裙",
                    },
                ],
                "reference_bindings": [
                    {
                        "index": 1,
                        "role": "character_identity",
                        "label": "老拐",
                        "source": "canonical_virtual_ip",
                        "url": "https://cdn.example/laoguai.png",
                    }
                ],
                "warnings": [],
            },
        }
    ]

    prompt = build_clip_storyboard_sheet_prompt(panels, style="3d_cartoon")

    assert "unmistakably non-photorealistic" in prompt
    assert "simplified sculpted face geometry" in prompt
    assert "reference photos define identity only" in prompt
    assert "never be mistaken for a photograph" in prompt


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
