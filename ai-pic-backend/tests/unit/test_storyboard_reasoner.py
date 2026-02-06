import json

import pytest
from app.services.storyboard_reasoner import (
    LANGGRAPH_AVAILABLE,
    StoryboardReActReasoner,
)

pytestmark = pytest.mark.skipif(
    not LANGGRAPH_AVAILABLE, reason="LangGraph not installed"
)


class DummyService:
    def __init__(self, plan_payload, frames_map):
        self.plan_payload = plan_payload
        self.frames_map = frames_map
        self.ai_manager = object()
        self.collected_scene_plans = []
        self.plan_calls = []

    async def generate_storyboard_plan(self, **_: object):
        self.plan_calls.append(_)
        return self.plan_payload

    async def generate_storyboard_from_plan_for_scene(
        self, *, scene_plan, **_: object
    ):  # noqa: ANN001
        self.collected_scene_plans.append(scene_plan.model_dump())
        return self.frames_map.get(scene_plan.scene_number)


def _get_duplicate_plan():
    return {
        "normalized": {
            "scenes": [
                {
                    "scene_number": 1,
                    "target_frames": 2,
                    "frames": [
                        {
                            "shot_type": "中景",
                            "camera_movement": "固定",
                            "composition": "三分法",
                            "intent": "对话",
                        },
                        {
                            "shot_type": "中景",
                            "camera_movement": "固定",
                            "composition": "三分法",
                            "intent": "对话",
                        },
                    ],
                }
            ]
        },
        "provider_used": "openai",
        "model_used": "gpt-4",
    }


def _get_multi_scene_plan():
    return {
        "normalized": {
            "scenes": [
                {
                    "scene_number": 1,
                    "target_frames": 1,
                    "frames": [
                        {
                            "shot_type": "远景",
                            "camera_movement": "推",
                            "composition": "三分法",
                            "intent": "开场",
                        }
                    ],
                },
                {
                    "scene_number": 2,
                    "target_frames": 1,
                    "frames": [
                        {
                            "shot_type": "近景",
                            "camera_movement": "拉",
                            "composition": "对称",
                            "intent": "转场",
                        }
                    ],
                },
            ]
        },
        "provider_used": "openai",
        "model_used": "gpt-4",
    }


@pytest.mark.asyncio
async def test_reasoner_skips_plan_when_no_scenes_and_no_scope():
    service = DummyService(plan_payload=_get_duplicate_plan(), frames_map={})
    reasoner = StoryboardReActReasoner(service)

    result = await reasoner.generate(
        script={"scenes": [], "dialogues": [], "stage_directions": []},
        frames_per_scene=2,
        max_frames=None,
        model=None,
        prefer_provider=None,
        temperature=0.6,
        selected_scenes=None,
    )

    assert result is None
    assert service.plan_calls == []
    assert service.collected_scene_plans == []


@pytest.mark.asyncio
async def test_reasoner_filters_plan_scenes_to_scope():
    frames_map = {
        1: [
            {
                "scene_number": 1,
                "shot_type": "远景",
                "camera_movement": "推",
                "composition": "三分法",
                "description": "场景1",
                "duration_seconds": 2,
                "ai_prompt": "test 1",
                "reference_images": [],
            }
        ],
        2: [
            {
                "scene_number": 2,
                "shot_type": "近景",
                "camera_movement": "拉",
                "composition": "对称",
                "description": "场景2",
                "duration_seconds": 2,
                "ai_prompt": "test 2",
                "reference_images": [],
            }
        ],
    }
    service = DummyService(
        plan_payload=_get_multi_scene_plan(),
        frames_map=frames_map,
    )
    reasoner = StoryboardReActReasoner(service)

    result = await reasoner.generate(
        script={"scenes": [], "dialogues": [], "stage_directions": []},
        frames_per_scene=1,
        max_frames=10,
        model=None,
        prefer_provider=None,
        temperature=0.7,
        selected_scenes=[1],
    )

    assert result is not None
    payload = json.loads(result["content"])
    assert {f["scene_number"] for f in payload["frames"]} == {1}
    assert [p["scene_number"] for p in service.collected_scene_plans] == [1]
    assert result["reasoning_trace"] == [
        "scenes_selected",
        "plan_ready",
        "plan_reviewed",
        "frames_generated",
        "frames_valid",
        "frames_ready",
    ]


@pytest.mark.asyncio
async def test_reasoner_normalizes_duplicate_plan_frames():
    service = DummyService(plan_payload=_get_duplicate_plan(), frames_map={1: None})
    reasoner = StoryboardReActReasoner(service)

    result = await reasoner.generate(
        script={"scenes": [], "dialogues": [], "stage_directions": []},
        frames_per_scene=2,
        max_frames=None,
        model="openai:gpt-4",
        prefer_provider="openai",
        temperature=0.6,
        selected_scenes=[1],
    )

    assert result is None  # frames generation failed -> fallback expected
    assert service.collected_scene_plans, "should attempt finalize with sanitized plan"
    outlines = service.collected_scene_plans[0]["frames"]
    combos = {(f["shot_type"], f["camera_movement"], f["intent"]) for f in outlines}
    assert len(combos) == len(outlines)


@pytest.mark.asyncio
async def test_reasoner_returns_frames_with_trace():
    frames_map = {
        1: [
            {
                "scene_number": 1,
                "shot_type": "远景",
                "camera_movement": "推",
                "composition": "三分法",
                "description": "夜市全景",
                "duration_seconds": 4,
                "ai_prompt": "test",
                "reference_images": [],
            },
            {
                "scene_number": 1,
                "shot_type": "近景",
                "camera_movement": "拉",
                "composition": "对称",
                "description": "角色特写",
                "duration_seconds": 3,
                "ai_prompt": "test 2",
                "reference_images": [],
            },
        ]
    }
    service = DummyService(plan_payload=_get_duplicate_plan(), frames_map=frames_map)
    reasoner = StoryboardReActReasoner(service)

    result = await reasoner.generate(
        script={"scenes": [], "dialogues": [], "stage_directions": []},
        frames_per_scene=2,
        max_frames=10,
        model=None,
        prefer_provider=None,
        temperature=0.7,
        selected_scenes=[1],
    )

    assert result is not None
    payload = json.loads(result["content"])
    assert payload["frames"], "frames should be present"
    assert result["reasoning_trace"] == [
        "scenes_selected",
        "plan_ready",
        "plan_reviewed",
        "frames_generated",
        "frames_valid",
        "frames_ready",
    ]
    assert (
        service.collected_scene_plans
        and len(service.collected_scene_plans[0]["frames"]) == 2
    )


@pytest.mark.asyncio
async def test_reasoner_returns_none_when_plan_fails():
    service = DummyService(plan_payload=None, frames_map={})
    reasoner = StoryboardReActReasoner(service)

    result = await reasoner.generate(
        script={"scenes": [], "dialogues": [], "stage_directions": []},
        frames_per_scene=2,
        max_frames=None,
        model=None,
        prefer_provider=None,
        temperature=0.5,
        selected_scenes=[1],
    )

    assert result is None
    assert len(service.plan_calls) == 1
    assert service.collected_scene_plans == []
