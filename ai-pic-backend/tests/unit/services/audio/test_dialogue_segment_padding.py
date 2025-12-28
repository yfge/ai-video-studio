"""Tests for scene segment padding to target duration."""

import pytest

from app.services.audio.dialogue_processor import plan_scene_segments_intelligent


def _planned_total_ms(segments, dialogue_ms: int) -> int:
    non_dialogue_ms = sum(
        int(getattr(seg, "planned_duration_ms", 0) or 0)
        for seg in segments
        if getattr(seg, "kind", "") in {"action", "pause"}
    )
    return int(dialogue_ms + non_dialogue_ms)


@pytest.mark.asyncio
async def test_padding_extends_action_segments_beyond_default_cap():
    dialogues = [
        {"character": "A", "content": "Hello", "actual_duration_ms": 2000},
        {"character": "B", "content": "World", "actual_duration_ms": 2000},
    ]
    stage_directions = [
        {"scene_number": 1, "timing": "mid", "content": "x"},  # short action beat
    ]

    target_seconds = 10
    segments = await plan_scene_segments_intelligent(
        dialogues=dialogues,
        stage_directions=stage_directions,
        scene_context={"scene_id": 1, "scene_number": 1},
        ai_service=None,
        use_intelligent_timing=False,
        target_duration_seconds=target_seconds,
    )

    assert segments
    assert _planned_total_ms(segments, dialogue_ms=4000) == target_seconds * 1000

    action_durations = [
        int(seg.planned_duration_ms or 0) for seg in segments if seg.kind == "action"
    ]
    assert action_durations, "expected at least one action segment"
    # Default action cap during planning is 3000ms; padding should be able to exceed it.
    assert max(action_durations) > 3000


@pytest.mark.asyncio
async def test_padding_falls_back_to_pause_when_no_actions():
    dialogues = [
        {"character": "A", "content": "Hello", "actual_duration_ms": 2000},
        {"character": "B", "content": "World", "actual_duration_ms": 2000},
    ]

    target_seconds = 10
    segments = await plan_scene_segments_intelligent(
        dialogues=dialogues,
        stage_directions=[],
        scene_context={"scene_id": 1, "scene_number": 1},
        ai_service=None,
        use_intelligent_timing=False,
        target_duration_seconds=target_seconds,
    )

    assert segments
    assert _planned_total_ms(segments, dialogue_ms=4000) == target_seconds * 1000

    pause_durations = [
        int(seg.planned_duration_ms or 0) for seg in segments if seg.kind == "pause"
    ]
    assert pause_durations, "expected pause segments"
    assert max(pause_durations) > 3000


@pytest.mark.asyncio
async def test_padding_trims_non_dialogue_when_dialogue_near_target():
    dialogues = [
        {"character": "A", "content": "Hello", "actual_duration_ms": 14000},
    ]
    stage_directions = [
        {
            "scene_number": 1,
            "timing": "mid",
            "content": "x"
            * 500,  # would cap to 3000ms action, exceeding remaining 1000ms
        },
    ]

    target_seconds = 15
    segments = await plan_scene_segments_intelligent(
        dialogues=dialogues,
        stage_directions=stage_directions,
        scene_context={"scene_id": 1, "scene_number": 1},
        ai_service=None,
        use_intelligent_timing=False,
        target_duration_seconds=target_seconds,
    )

    assert segments
    assert _planned_total_ms(segments, dialogue_ms=14000) == target_seconds * 1000

    non_dialogue_ms = sum(
        int(getattr(seg, "planned_duration_ms", 0) or 0)
        for seg in segments
        if getattr(seg, "kind", "") in {"action", "pause"}
    )
    assert non_dialogue_ms == 1000
