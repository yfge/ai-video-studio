from app.models.story_structure import Scene, SceneBeat
from app.services.audio.episode_timeline_beats import build_episode_timeline_beats
from app.services.audio.storyboard_from_timeline import (
    build_storyboard_frames_from_audio_timeline,
)


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


def test_build_storyboard_frames_from_audio_timeline_merges_short_pauses() -> None:
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
    assert [f["end_ms"] for f in frames] == [2000, 3500, 6000]


def test_audio_timeline_storyboard_ai_prompt_does_not_leak_dialogue_text() -> None:
    """Dialogue text can be shown in UI via `description`, but must not leak into ai_prompt."""
    from app.services.storyboard.storyboard_prompt_utils import (
        apply_storyboard_prompt_optimizations,
    )

    audio_timeline = {
        "beats": [
            {
                "scene_id": 1,
                "scene_number": 1,
                "beat_id": 11,
                "beat_type": "dialogue",
                "speaker_name": "林晚",
                "text": "你给我解释清楚！",
                "start_ms": 0,
                "end_ms": 1000,
            }
        ]
    }

    frames = build_storyboard_frames_from_audio_timeline(audio_timeline=audio_timeline)
    apply_storyboard_prompt_optimizations(frames)

    assert "你给我解释清楚" in frames[0]["description"]
    assert "你给我解释清楚" not in (frames[0].get("ai_prompt") or "")
    assert "开口说话" in (frames[0].get("ai_prompt") or "")
    assert "无字幕" in (frames[0].get("ai_prompt") or "")


def test_audio_timeline_storyboard_prompt_description_blurs_readable_text() -> None:
    from app.services.storyboard.storyboard_prompt_utils import (
        apply_storyboard_prompt_optimizations,
    )

    audio_timeline = {
        "beats": [
            {
                "scene_id": 1,
                "scene_number": 1,
                "beat_id": 11,
                "beat_type": "dialogue",
                "speaker_name": "林晚",
                "text": "离婚协议.pdf 你到底想干什么？",
                "start_ms": 0,
                "end_ms": 1000,
            }
        ]
    }

    frames = build_storyboard_frames_from_audio_timeline(audio_timeline=audio_timeline)
    apply_storyboard_prompt_optimizations(frames)

    assert "屏幕文字模糊不可读" in (frames[0].get("ai_prompt") or "")
    assert ".pdf" not in (frames[0].get("ai_prompt") or "").lower()
