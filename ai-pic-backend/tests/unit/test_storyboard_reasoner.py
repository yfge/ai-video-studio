import json
import pytest

from app.services.storyboard_reasoner import StoryboardReActReasoner, LANGGRAPH_AVAILABLE

pytestmark = pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")


class DummyService:
    def __init__(self, plan_payload, frames_map):
        self.plan_payload = plan_payload
        self.frames_map = frames_map
        self.ai_manager = object()
        self.collected_scene_plans = []

    async def generate_storyboard_plan(self, **_: object):
        return self.plan_payload

    async def generate_storyboard_from_plan_for_scene(self, *, scene_plan, **_: object):  # noqa: ANN001
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
                        {"shot_type": "中景", "camera_movement": "固定", "composition": "三分法", "intent": "对话"},
                        {"shot_type": "中景", "camera_movement": "固定", "composition": "三分法", "intent": "对话"},
                    ],
                }
            ]
        },
        "provider_used": "openai",
        "model_used": "gpt-4",
    }


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
            }
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
    assert result["reasoning_trace"] == ["plan_ready", "plan_reviewed", "frames_ready"]
    assert service.collected_scene_plans and len(service.collected_scene_plans[0]["frames"]) == 2


@pytest.mark.asyncio
async def test_reasoner_returns_none_when_plan_fails():
    service = DummyService(plan_payload=None, frames_map={})
    reasoner = StoryboardReActReasoner(service)

    result = await reasoner.generate(
        script={},
        frames_per_scene=2,
        max_frames=None,
        model=None,
        prefer_provider=None,
        temperature=0.5,
        selected_scenes=None,
    )

    assert result is None
