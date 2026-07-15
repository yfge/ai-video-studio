from app.services.storyboard.clip_storyboard_panel_sanitizer import (
    sanitize_clip_storyboard_panels,
)


def test_sanitizer_replaces_stale_cast_and_style_throughout_panel_payload():
    panel = {
        "panel_index": 2,
        "clip_id": "clip-1",
        "visual_prompt": (
            "A confident middle-aged man faces a younger, slightly awkward man. "
            "Moment 2 at 4000ms: younger man looks around nervously"
        ),
        "video_prompt": (
            "Plot: 老拐站在客厅中央，阿盖儿站在他面前。 "
            "Dialogue: (silent pause) "
            "Character anchor: A confident middle-aged man with short gray hair. "
            "Camera: Wide shot. "
            "Action: The older man gestures while the younger man looks around. "
            "Style: 3D cartoon. "
            "Duration: 12833ms."
        ),
        "direction_anchor": "older man watches younger man",
        "aesthetic_reference": "Pixar-style 3D animation",
        "composition_geometry": (
            "Two subjects, older man center-left, younger man center-right"
        ),
        "motion_timeline": [
            {"at_ms": 0, "action": "both stand still"},
            {"at_ms": 4000, "action": "younger man looks around nervously"},
        ],
        "emotional_landing": "older man stays calm",
        "source_refs": {
            "scene_beat_id": 99,
            "timeline_shot_plan": {
                "visual_prompt": "A confident middle-aged man",
                "aesthetic_reference": "Pixar-style 3D animation",
            },
        },
        "bound_context": {
            "characters": [
                {"name": "老拐", "anchor_url": "https://cdn.example/laoguai.png"},
                {"name": "阿盖儿", "anchor_url": "https://cdn.example/agaier.png"},
            ]
        },
    }

    result = sanitize_clip_storyboard_panels([panel], style="live_action")[0]

    assert result["visual_prompt"] == (
        "老拐站在客厅中央，阿盖儿站在他面前。 "
        "Moment 2 at 4000ms: 阿盖儿 looks around nervously"
    )
    assert "Character anchor:" not in result["video_prompt"]
    assert "Style:" not in result["video_prompt"]
    assert "middle-aged man" not in result["video_prompt"]
    assert "younger man" not in result["video_prompt"]
    assert "老拐 gestures" in result["video_prompt"]
    assert "阿盖儿 looks around" in result["video_prompt"]
    assert result["direction_anchor"] == "老拐 watches 阿盖儿"
    assert result["aesthetic_reference"] == ""
    assert result["composition_geometry"] == (
        "老拐 and 阿盖儿, 老拐 center-left, 阿盖儿 center-right"
    )
    assert result["motion_timeline"] == [
        {"at_ms": 0, "action": "老拐 and 阿盖儿 stand still"},
        {"at_ms": 4000, "action": "阿盖儿 looks around nervously"},
    ]
    assert result["source_refs"] == {"scene_beat_id": 99}
    assert "Pixar" not in result["storyboard_panel_prompt"]
    assert "3D cartoon" not in result["storyboard_panel_prompt"]
    assert "老拐" in result["storyboard_panel_prompt"]
    assert "阿盖儿" in result["storyboard_panel_prompt"]
