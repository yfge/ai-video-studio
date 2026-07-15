from app.services.storyboard.clip_storyboard_video_sequence_prompt import (
    build_clip_storyboard_sequence_video_prompt,
)


def test_sequence_prompt_animates_all_panels_in_order_without_collage_output():
    panels = _panels(relative_motion=True)

    prompt = build_clip_storyboard_sequence_video_prompt(
        panels,
        clip_id="video_scene_91_beat_4001_011",
        duration_seconds=6.26,
    )

    assert "entire clip storyboard sheet" in prompt
    assert "6.260-second Timeline clip" in prompt
    assert "left-to-right, top-to-bottom" in prompt
    assert "not a simultaneous collage" in prompt
    assert "Never reveal or animate the sheet" in prompt
    assert "exactly one camera view filling the complete output frame" in prompt
    assert "Never stack, tile, duplicate" in prompt
    assert "Panel 1 at 0.000s: 老拐递出手机" in prompt
    assert "Panel 2 at 2.000s: 阿盖儿接过手机" in prompt
    assert "Panel 3 at 4.000s: 老拐滑动屏幕" in prompt
    assert "Panel 4 at 6.000s: 两人共同看向手机" in prompt
    assert "Use panel 1 only" not in prompt


def test_sequence_prompt_normalizes_absolute_fallback_timestamps():
    panels = _panels(relative_motion=False)

    prompt = build_clip_storyboard_sequence_video_prompt(
        panels,
        clip_id="clip-absolute",
        duration_seconds=6.26,
        prompt_override="保持手机交接动作自然连贯",
    )

    assert "Operator motion direction: 保持手机交接动作自然连贯" in prompt
    assert "Panel 1 at 0.000s" in prompt
    assert "Panel 2 at 2.000s" in prompt
    assert "Panel 4 at 6.000s" in prompt


def test_two_panel_sequence_uses_first_and_last_motion_anchors():
    panels = _panels(relative_motion=True)[:2]

    prompt = build_clip_storyboard_sequence_video_prompt(
        panels,
        clip_id="clip-two-panel",
        duration_seconds=6.26,
    )

    assert "Panel 1 at 0.000s: 老拐递出手机" in prompt
    assert "Panel 2 at 6.000s: 两人共同看向手机" in prompt


def _panels(*, relative_motion: bool) -> list[dict]:
    actions = [
        "老拐递出手机",
        "阿盖儿接过手机",
        "老拐滑动屏幕",
        "两人共同看向手机",
    ]
    base = 0 if relative_motion else 30000
    motion = [
        {"at_ms": base + index * 2000, "action": action}
        for index, action in enumerate(actions)
    ]
    return [
        {
            "panel_id": f"clip_storyboard_panel_{index:03d}",
            "panel_index": index,
            "start_ms": 30000,
            "end_ms": 36260,
            "shot_type": shot_type,
            "composition_geometry": f"composition {index}",
            "motion_timeline": motion,
            "video_prompt": "老拐把手机交给阿盖儿并展示外卖应用",
        }
        for index, shot_type in enumerate(
            [
                "wide establishing shot",
                "medium two-shot",
                "insert detail shot",
                "held closing shot",
            ],
            start=1,
        )
    ]
