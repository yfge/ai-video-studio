from app.services.storyboard.storyboard_prompt_compiler import StoryboardPromptCompiler


def test_storyboard_prompt_compiler_preserves_shot_plan_sections():
    frame = {
        "frame_number": 1,
        "timeline_clip_id": "video_scene_1_beat_1_001",
        "scene_id": 12,
        "beat_id": 34,
        "description": "林晚站在雨夜门口",
        "shot_type": "中景",
        "camera_movement": "缓慢推进",
        "composition": "林晚在左三分线，门框切分右侧负空间",
        "reference_images": ["https://cdn.example/linwan.png"],
        "shot_plan_prompt_layers": {
            "direction_anchor": "朝向雨夜门口的孤独寻找",
            "aesthetic_reference": "IMAX film, Panavision C lens, cold neon rain",
            "composition_geometry": "left third subject, doorway as vertical split",
            "motion_timeline": [
                {"at_ms": 0, "action": "林晚停在门口"},
                {"at_ms": 1400, "action": "雨水落在肩头"},
                {"at_ms": 2800, "action": "她抬头看向门内"},
            ],
            "emotional_landing": "冷雨中的克制孤独",
        },
    }

    compiled = StoryboardPromptCompiler().compile_frame(
        frame,
        reference_notes=[{"type": "character", "name": "林晚"}],
        provider="openai",
        negative_prompt_supported=False,
    )

    assert compiled["version"] == "storyboard_prompt_v2"
    assert compiled["clip_identity"]["timeline_clip_id"] == "video_scene_1_beat_1_001"
    assert "Direction anchor: 朝向雨夜门口的孤独寻找" in compiled["image_prompt"]
    assert "Aesthetic reference: IMAX film" in compiled["image_prompt"]
    assert "Composition geometry: left third subject" in compiled["image_prompt"]
    assert "0ms: 林晚停在门口" in compiled["image_prompt"]
    assert "Emotional landing: 冷雨中的克制孤独" in compiled["image_prompt"]
    assert "No readable text" in compiled["image_prompt"]
    assert "negative_prompt not supported; constraints inlined" in compiled["warnings"]
    assert len(compiled["prompt_sha256"]) == 64


def test_storyboard_prompt_compiler_reads_timeline_shot_plan_from_source_refs():
    frame = {
        "description": "门口短暂停顿",
        "source_refs": {
            "timeline_shot_plan": {
                "clip_id": "clip_from_timeline",
                "scene_id": "scene-1",
                "beat_id": "beat-2",
                "direction_anchor": "从门外向内窥见紧张气氛",
                "aesthetic_reference": "cool tungsten contrast",
                "composition_geometry": "door frame splits foreground and background",
                "motion_timeline": [
                    {"at_ms": 0, "action": "hand reaches toward the handle"},
                    {"at_ms": 900, "action": "the hand stops before touching it"},
                ],
                "emotional_landing": "suspended hesitation",
            }
        },
    }

    compiled = StoryboardPromptCompiler().compile_frame(frame)

    assert compiled["clip_identity"]["timeline_clip_id"] == "clip_from_timeline"
    assert "Direction anchor: 从门外向内窥见紧张气氛" in compiled["image_prompt"]
    assert "door frame splits foreground" in compiled["image_prompt"]
    assert "the hand stops before touching it" in compiled["i2v_motion_prompt"]


def test_storyboard_prompt_compiler_builds_distinct_keyframe_prompts():
    frame = {
        "description": "陈哲坐在车内，侧脸被手机屏照亮",
        "shot_plan_prompt_layers": {
            "motion_timeline": [
                {"at_ms": 0, "action": "他低头盯着屏幕"},
                {"at_ms": 2200, "action": "他迟疑后抬眼看向窗外"},
            ]
        },
    }

    compiled = StoryboardPromptCompiler().compile_frame(frame)

    assert compiled["start_keyframe_prompt"] != compiled["end_keyframe_prompt"]
    assert "Opening keyframe" in compiled["start_keyframe_prompt"]
    assert "他低头盯着屏幕" in compiled["start_keyframe_prompt"]
    assert "Ending keyframe" in compiled["end_keyframe_prompt"]
    assert "他迟疑后抬眼看向窗外" in compiled["end_keyframe_prompt"]


def test_storyboard_prompt_compiler_i2v_prompt_focuses_on_motion_not_reference_visuals():
    frame = {
        "description": "穿深色西装的男人坐在车内，雨夜霓虹反射在车窗上",
        "shot_plan_prompt_layers": {
            "camera_movement": "locked tripod shot",
            "motion_timeline": [
                {"at_ms": 0, "action": "the subject remains still"},
                {"at_ms": 1200, "action": "rain moves across the window"},
                {"at_ms": 2400, "action": "the subject slowly turns his eyes"},
            ],
        },
    }

    compiled = StoryboardPromptCompiler().compile_frame(frame)

    assert "Use the reference image for identity" in compiled["i2v_motion_prompt"]
    assert "Motion timeline:" in compiled["i2v_motion_prompt"]
    assert "the subject slowly turns his eyes" in compiled["i2v_motion_prompt"]
    assert "dark suit" not in compiled["i2v_motion_prompt"].lower()
    assert "neon" not in compiled["i2v_motion_prompt"].lower()
