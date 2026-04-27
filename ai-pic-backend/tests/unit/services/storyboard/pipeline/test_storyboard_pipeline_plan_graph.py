"""LangGraph plan-node regression tests for StoryboardPipeline."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from app.services.storyboard.pipeline.pipeline_context import PipelineContext
from app.services.storyboard.pipeline.pipeline_state import (
    PipelineState,
    ValidationResult,
)


@pytest.mark.asyncio
async def test_execute_langgraph_uses_explicit_plan_and_honors_max_frames():
    """LangGraph path should generate from plan without nesting the reasoner."""
    from app.services.storyboard.pipeline.storyboard_pipeline import (
        LANGGRAPH_AVAILABLE,
        StoryboardPipeline,
    )

    if not LANGGRAPH_AVAILABLE:
        pytest.skip("langgraph not available")

    class DummyAIService:
        def __init__(self):
            self.scene_max_frames = []
            self.direct_calls = 0

        async def generate_storyboard_plan(self, **kwargs):
            assert kwargs["model"] == "story-model"
            assert kwargs["prefer_provider"] == "story-provider"
            assert kwargs["frames_per_scene"] == 2
            assert kwargs["selected_scenes"] == [1]
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
                                    "intent": "establish",
                                },
                                {
                                    "shot_type": "近景",
                                    "camera_movement": "推",
                                    "composition": "对称",
                                    "intent": "reaction",
                                },
                            ],
                        }
                    ]
                },
                "provider_used": "story-provider",
                "model_used": "story-model",
                "usage": {"prompt_tokens": 10},
            }

        async def generate_storyboard_from_plan_for_scene(self, **kwargs):
            self.scene_max_frames.append(kwargs["max_frames"])
            return [
                {
                    "frame_id": "f1",
                    "frame_number": 1,
                    "scene_number": 1,
                    "description": "Frame 1",
                },
                {
                    "frame_id": "f2",
                    "frame_number": 2,
                    "scene_number": 1,
                    "description": "Frame 2",
                },
            ]

        async def generate_storyboard(self, **kwargs):
            self.direct_calls += 1
            raise AssertionError(
                "Pipeline should not call nested storyboard generation"
            )

    class NoopValidator:
        def __init__(self, name):
            self.name = name

        def validate(self, state, context):
            return [ValidationResult.success(self.name)]

    ai_service = DummyAIService()
    pipeline = StoryboardPipeline(MagicMock(), ai_service=ai_service)
    pipeline.validators = {name: NoopValidator(name) for name in pipeline.validators}

    script = SimpleNamespace(
        id=1,
        content="Scene content",
        scenes=[{"scene_number": 1, "description": "A room"}],
        dialogues=[{"scene_number": 1, "character": "A", "content": "Hi"}],
        stage_directions=[],
        extra_metadata={},
    )
    state = PipelineState(
        script_id=1,
        frames_per_scene=2,
        selected_scenes=[1],
    )
    state.model = "story-model"
    state.prefer_provider = "story-provider"
    state.max_frames = 1

    with patch.object(pipeline.precheck, "check_from_context") as mock_check:
        mock_check.return_value = MagicMock(ready=True, errors=[])
        result = await pipeline._execute_langgraph(
            state, PipelineContext(script_id=1), script, None
        )

    assert result["success"] is True
    assert result["frame_count"] == 1
    assert result["plan"]["scenes"][0]["scene_number"] == 1
    assert ai_service.direct_calls == 0
    assert ai_service.scene_max_frames == [1]
