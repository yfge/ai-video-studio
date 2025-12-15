from app.models.story_structure import Scene, SceneBeat
from app.services.dialogue_audio_service import (
    build_episode_timeline_beats,
    build_storyboard_frames_from_audio_timeline,
    plan_scene_segments,
)


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


def test_build_episode_timeline_beats_offsets_scene_windows() -> None:
    scene1 = Scene(id=1, script_id=1, scene_number="1", slug_line="S1")
    scene2 = Scene(id=2, script_id=1, scene_number="2", slug_line="S2")

    beats_by_scene = {
        1: [
            SceneBeat(
                id=11,
                scene_id=1,
                order_index=1,
                beat_type="dialogue",
                dialogue_excerpt="你好",
                duration_seconds=1.0,
                extra_metadata={"start_ms": 0, "end_ms": 1000, "speaker_name": "小明"},
            ),
            SceneBeat(
                id=12,
                scene_id=1,
                order_index=2,
                beat_type="pause",
                duration_seconds=0.5,
                extra_metadata={"start_ms": 1000, "end_ms": 1500},
            ),
        ],
        2: [
            SceneBeat(
                id=21,
                scene_id=2,
                order_index=1,
                beat_type="action",
                beat_summary="（走向门口）",
                duration_seconds=2.0,
                extra_metadata={"start_ms": 0, "end_ms": 2000},
            )
        ],
    }

    beats, total_ms = build_episode_timeline_beats(
        scenes=[scene1, scene2],
        beats_by_scene_id=beats_by_scene,
    )

    assert total_ms == 3500
    assert [b["start_ms"] for b in beats] == [0, 1000, 1500]
    assert [b["end_ms"] for b in beats] == [1000, 1500, 3500]


def test_build_storyboard_frames_from_audio_timeline_filters_pauses() -> None:
    audio_timeline = {
        "beats": [
            {
                "scene_id": 1,
                "scene_number": 1,
                "beat_id": 11,
                "beat_type": "dialogue",
                "speaker_name": "小明",
                "text": "你好",
                "start_ms": 0,
                "end_ms": 1000,
            },
            {
                "scene_id": 1,
                "scene_number": 1,
                "beat_id": 12,
                "beat_type": "pause",
                "speaker_name": None,
                "text": None,
                "start_ms": 1000,
                "end_ms": 2000,
            },
            {
                "scene_id": 1,
                "scene_number": 1,
                "beat_id": 13,
                "beat_type": "action",
                "speaker_name": None,
                "text": "（转身）",
                "start_ms": 2000,
                "end_ms": 3500,
            },
            {
                "scene_id": 1,
                "scene_number": 1,
                "beat_id": 14,
                "beat_type": "pause",
                "speaker_name": None,
                "text": None,
                "start_ms": 3500,
                "end_ms": 6000,
            },
        ]
    }

    frames = build_storyboard_frames_from_audio_timeline(
        audio_timeline=audio_timeline,
        min_pause_duration_ms=1500,
    )
    assert [f["start_ms"] for f in frames] == [0, 2000, 3500]
    assert [f["end_ms"] for f in frames] == [1000, 3500, 6000]
