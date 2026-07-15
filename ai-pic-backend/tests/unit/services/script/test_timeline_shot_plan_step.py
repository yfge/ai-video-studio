from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.services.script import timeline_shot_plan_step


def _shot(clip_id: str, duration_ms: int) -> dict:
    return {
        "clip_id": clip_id,
        "duration_ms": duration_ms,
        "plot": "角色发现异常",
        "dialogue_source": "角色：这里不对劲。",
        "visual_prompt": "卡通角色站在发光门前",
        "video_prompt": "角色走向发光门，镜头缓慢推近",
        "character_anchor": "蓝色外套的卡通角色",
        "camera": "medium shot",
        "action": "走向发光门",
        "direction_anchor": "悬念发现",
        "aesthetic_reference": "stylized 3D animation",
        "shot_type": "medium shot",
        "camera_movement": "slow push-in",
        "composition_geometry": "角色居中，门在背景右侧",
        "motion_timeline": [
            {"at_ms": 0, "action": "角色抬头"},
            {"at_ms": duration_ms, "action": "角色走到门前"},
        ],
        "emotional_landing": "冷色悬念",
        "prompt_method": "direction_reference_geometry_timeline_emotion_v1",
    }


def _timeline(*, include_plan: bool) -> SimpleNamespace:
    clip_id = "video_scene_1_beat_1_001"
    duration_ms = 2000
    source_refs = {}
    if include_plan:
        source_refs["timeline_shot_plan"] = _shot(clip_id, duration_ms)
    return SimpleNamespace(
        version=7,
        spec={
            "tracks": [
                {
                    "track_type": "video",
                    "clips": [
                        {
                            "clip_id": clip_id,
                            "track_type": "video",
                            "duration_ms": duration_ms,
                            "text": "角色发现异常",
                            "source_refs": source_refs,
                        }
                    ],
                },
                {
                    "track_type": "dialogue",
                    "clips": [
                        {
                            "clip_id": "dialogue_scene_1_beat_1_001",
                            "scene_id": None,
                            "beat_id": None,
                            "text": "角色：这里不对劲。",
                        }
                    ],
                },
            ]
        },
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_reuses_complete_current_shot_plan(monkeypatch) -> None:
    timeline = _timeline(include_plan=True)

    class _UnexpectedService:
        def __init__(self, _db) -> None:
            raise AssertionError("complete shot plan should be reused")

    monkeypatch.setattr(
        timeline_shot_plan_step,
        "TimelineShotPlanService",
        _UnexpectedService,
    )

    result = (
        await timeline_shot_plan_step.generate_timeline_shot_plan_from_current_version(
            object(), timeline, user_id=1
        )
    )

    assert result is timeline


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generates_when_current_shot_plan_is_missing(monkeypatch) -> None:
    timeline = _timeline(include_plan=False)
    generated = SimpleNamespace(version=8, spec={})

    class _ExpectedService:
        def __init__(self, _db) -> None:
            pass

        async def generate_shot_plan_for_timeline(self, *args, **kwargs):
            return generated

    monkeypatch.setattr(
        timeline_shot_plan_step,
        "TimelineShotPlanService",
        _ExpectedService,
    )

    result = (
        await timeline_shot_plan_step.generate_timeline_shot_plan_from_current_version(
            object(), timeline, user_id=1
        )
    )

    assert result is generated
