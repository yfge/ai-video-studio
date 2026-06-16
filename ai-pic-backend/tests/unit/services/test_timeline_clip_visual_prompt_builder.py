from app.services.timeline_clip_visual_prompt_builder import (
    PROMPT_CONTRACT_VERSION,
    build_timeline_clip_keyframe_frames,
    build_timeline_clip_video_motion_prompt,
)


def clip_with_motion_plan() -> dict:
    return {
        "clip_id": "video_scene_001_beat_002_001",
        "track_type": "video",
        "text": "陈哲坐在车内，侧脸被手机屏照亮。",
        "source_refs": {
            "timeline_shot_plan": {
                "visual_prompt": "陈哲坐在雨夜车内，手机屏幕冷光照亮侧脸",
                "video_prompt": "镜头缓慢推近，雨水沿车窗滑落",
                "direction_anchor": "雨夜车内的迟疑与警觉",
                "aesthetic_reference": "live action cinema, cool neon rain",
                "shot_type": "tight medium close-up",
                "camera_movement": "slow push-in",
                "composition_geometry": "face on right third, window reflections left",
                "motion_timeline": [
                    {"at_ms": 0, "action": "他低头盯着手机屏幕"},
                    {"at_ms": 900, "action": "他的手指停在拨号键上"},
                    {"at_ms": 1800, "action": "他抬眼看向雨中的车窗"},
                ],
                "emotional_landing": "克制的怀疑落点",
            }
        },
    }


def test_keyframe_prompts_use_first_and_last_motion_points() -> None:
    frames, metadata = build_timeline_clip_keyframe_frames(clip_with_motion_plan())

    assert [frame["role"] for frame in frames] == ["start_frame", "end_frame"]
    assert "他低头盯着手机屏幕" in frames[0]["prompt"]
    assert "他抬眼看向雨中的车窗" in frames[1]["prompt"]
    assert frames[0]["prompt"] != frames[1]["prompt"]
    assert metadata["prompt_contract_version"] == PROMPT_CONTRACT_VERSION
    assert metadata["visual_prompt_source"] == "timeline_shot_plan.visual_prompt"
    assert metadata["motion_prompt_source"] == "timeline_shot_plan.video_prompt"


def test_video_motion_prompt_prefers_operator_override() -> None:
    prompt, metadata = build_timeline_clip_video_motion_prompt(
        clip_with_motion_plan(),
        override="只保留轻微呼吸和窗外雨滴，镜头固定",
    )

    assert "只保留轻微呼吸和窗外雨滴" in prompt
    assert "slow push-in" not in prompt
    assert metadata["motion_prompt_source"] == "operator_override"


def test_video_motion_prompt_without_override_keeps_motion_and_constraints() -> None:
    prompt, metadata = build_timeline_clip_video_motion_prompt(clip_with_motion_plan())

    assert "Generate only the selected Timeline clip" in prompt
    assert "slow push-in" in prompt
    assert "0ms: 他低头盯着手机屏幕" in prompt
    assert "1800ms: 他抬眼看向雨中的车窗" in prompt
    assert "No subtitles" in prompt
    assert metadata["prompt_contract_version"] == PROMPT_CONTRACT_VERSION
