from app.services.dialogue_audio_service import plan_scene_segments


def test_plan_scene_segments_orders_stage_and_dialogue() -> None:
    dialogues = [{"character": "小明", "content": "你好"}]
    stage = [
        {"content": "（开场动作）", "timing": "start"},
        {"content": "（中段动作）", "timing": "mid"},
        {"content": "（收尾动作）", "timing": "end"},
    ]

    segments = plan_scene_segments(
        dialogues=dialogues,
        stage_directions=stage,
        pause_after_dialogue_ms=300,
        action_base_ms=800,
        action_per_char_ms=0,
        action_max_ms=3000,
    )

    assert [s.kind for s in segments] == [
        "action",
        "dialogue",
        "pause",
        "action",
        "pause",
        "action",
        "pause",
    ]
    assert segments[0].planned_duration_ms == 800
    assert segments[0].timing == "start"
    assert segments[3].timing == "mid"
    assert segments[5].timing == "end"


def test_plan_scene_segments_falls_back_when_no_content() -> None:
    segments = plan_scene_segments(dialogues=[], stage_directions=[])
    assert len(segments) == 1
    assert segments[0].kind == "action"
    assert segments[0].planned_duration_ms == 2000


def test_plan_scene_segments_treats_silence_dialogue_as_pause() -> None:
    segments = plan_scene_segments(
        dialogues=[{"character": "旁白", "content": "..."}],
        stage_directions=[],
        pause_after_dialogue_ms=300,
    )
    assert [s.kind for s in segments] == ["pause", "pause"]
    assert segments[0].planned_duration_ms == 800
    assert segments[1].planned_duration_ms == 300
