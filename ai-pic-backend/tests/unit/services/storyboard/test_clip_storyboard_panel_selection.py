from app.services.storyboard.clip_storyboard_panel_selection import (
    select_clip_storyboard_panel_count,
)


def test_auto_panel_count_uses_structured_visual_beats_with_duration_cap():
    clip = _clip(
        duration_ms=6260,
        actions=[
            "老拐递出手机",
            "阿盖儿接过手机",
            "老拐滑动屏幕",
            "两人共同看向手机",
        ],
    )

    selection = select_clip_storyboard_panel_count(clip, None)

    assert selection.panel_count == 4
    assert selection.mode == "auto"
    assert selection.visual_beat_count == 4
    assert selection.reason == "structured_visual_beats"


def test_auto_panel_count_limits_dense_short_motion_to_two_panels():
    clip = _clip(
        duration_ms=1400,
        actions=["抬头", "转向窗外", "凝视远方"],
    )

    selection = select_clip_storyboard_panel_count(clip, None)

    assert selection.panel_count == 2
    assert selection.visual_beat_count == 3


def test_auto_panel_count_uses_six_and_reserves_nine_for_long_complex_clips():
    medium = select_clip_storyboard_panel_count(
        _clip(duration_ms=15000, actions=[f"动作{i}" for i in range(7)]),
        None,
    )
    long = select_clip_storyboard_panel_count(
        _clip(duration_ms=18000, actions=[f"动作{i}" for i in range(8)]),
        None,
    )

    assert medium.panel_count == 6
    assert long.panel_count == 9


def test_fixed_panel_count_stays_operator_controlled_and_normalized():
    selection = select_clip_storyboard_panel_count(
        _clip(duration_ms=6260, actions=["递出", "接过"]),
        3,
    )

    assert selection.panel_count == 4
    assert selection.mode == "fixed"
    assert selection.reason == "operator_requested_panel_count"


def test_auto_panel_count_falls_back_to_duration_without_motion_timeline():
    selection = select_clip_storyboard_panel_count(
        {"start_ms": 0, "end_ms": 12000, "source_refs": {}},
        None,
    )

    assert selection.panel_count == 6
    assert selection.visual_beat_count == 0
    assert selection.reason == "duration_fallback_no_structured_beats"


def _clip(*, duration_ms: int, actions: list[str]) -> dict:
    step = duration_ms // max(1, len(actions))
    return {
        "start_ms": 30000,
        "end_ms": 30000 + duration_ms,
        "source_refs": {
            "timeline_shot_plan": {
                "motion_timeline": [
                    {"at_ms": index * step, "action": action}
                    for index, action in enumerate(actions)
                ]
            }
        },
    }
