from __future__ import annotations

from typing import Any

import pytest
from app.services.ai.scripts_ai_manager import (
    _DIALOGUE_MAX_TOKENS,
    _MAX_DIALOGUE_SCENES,
    _REPAIR_MAX_TOKENS,
    _SCENE_PLAN_MAX_TOKENS,
    ScriptManagerMixin,
)


class _DummyResponse:
    def __init__(
        self,
        *,
        success: bool,
        data: Any,
        provider: str = "minimax",
        model: str = "abab",
        usage: dict | None = None,
    ) -> None:
        self.success = success
        self.data = data
        self.provider = provider
        self.model = model
        self.usage = usage or {}


class _DummyManager:
    def __init__(self, responses: list[_DummyResponse]) -> None:
        self._responses = responses
        self.calls: list[dict[str, Any]] = []

    async def generate_text(self, **kwargs: Any):
        self.calls.append(kwargs)
        return self._responses.pop(0)


class _DummyService(ScriptManagerMixin):
    def __init__(self, *, ai_manager: _DummyManager) -> None:
        self.ai_manager = ai_manager

    def _build_script_text(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> str:
        return "ASSEMBLED"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_call_ai_manager_script_passes_max_tokens_and_repairs_json():
    planned_scenes = [
        {
            "scene_number": 1,
            "slug_line": "INT. Cafe - day",
            "location": "cafe",
            "time_of_day": "day",
            "summary": "opening",
            "estimated_duration_seconds": 30,
            "dialogue_ratio": 0.6,
        },
        {
            "scene_number": 2,
            "slug_line": "EXT. Street - night",
            "location": "street",
            "time_of_day": "night",
            "summary": "conflict",
            "estimated_duration_seconds": 45,
            "dialogue_ratio": 0.7,
        },
    ]

    manager = _DummyManager(
        [
            _DummyResponse(success=True, data={"scenes": planned_scenes}),
            _DummyResponse(success=True, data="```json\ninvalid\n```"),
            _DummyResponse(
                success=True,
                data={
                    "scenes": planned_scenes,
                    "dialogues": [
                        {
                            "scene_number": 1,
                            "character": "A",
                            "content": "hi",
                            "emotion": None,
                            "action": None,
                        }
                    ],
                    "stage_directions": [
                        {
                            "scene_number": 1,
                            "timing": "intro",
                            "content": "walks in",
                            "type": "action",
                        }
                    ],
                },
            ),
        ]
    )
    service = _DummyService(ai_manager=manager)

    result = await service._call_ai_manager_script(
        episode={"duration_minutes": 5, "scenes": []},
        story={"title": "T"},
        format_type="short_video",
        language="zh",
        dialogue_style="natural",
        scene_detail_level="medium",
        additional_requirements=None,
        style_preferences=None,
        model="minimax:abab",
        prefer_provider="minimax",
        temperature=0.7,
    )

    assert result is not None
    assert result["generation_method"] == "ai_manager_minimax"
    assert result["content"]["content"] == "ASSEMBLED"

    assert len(manager.calls) == 3
    assert manager.calls[0]["max_tokens"] == _SCENE_PLAN_MAX_TOKENS
    assert manager.calls[1]["max_tokens"] == _DIALOGUE_MAX_TOKENS
    assert manager.calls[2]["max_tokens"] == _REPAIR_MAX_TOKENS
    assert manager.calls[0]["json_schema"]["name"] == "script_scenes"
    assert manager.calls[1]["json_schema"]["name"] == "script_dialogues"
    assert manager.calls[2]["json_schema"]["name"] == "script_dialogues"
    assert manager.calls[0]["stream"] is False
    assert manager.calls[1]["stream"] is False
    assert manager.calls[2]["stream"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_call_ai_manager_script_replans_when_episode_scenes_too_many():
    original_scenes = [
        {
            "scene_number": idx,
            "slug_line": f"INT. S{idx} - day",
            "location": "room",
            "time_of_day": "day",
            "summary": f"beat {idx}",
        }
        for idx in range(1, _MAX_DIALOGUE_SCENES + 6)
    ]

    planned_scenes = [
        {
            "scene_number": 1,
            "slug_line": "INT. Room - day",
            "location": "room",
            "time_of_day": "day",
            "summary": "condensed",
            "estimated_duration_seconds": 60,
            "dialogue_ratio": 0.7,
        }
    ]

    manager = _DummyManager(
        [
            _DummyResponse(success=True, data={"scenes": planned_scenes}),
            _DummyResponse(
                success=True,
                data={
                    "scenes": planned_scenes,
                    "dialogues": [
                        {
                            "scene_number": 1,
                            "character": "A",
                            "content": "hi",
                            "emotion": None,
                            "action": None,
                        }
                    ],
                    "stage_directions": [],
                },
            ),
        ]
    )
    service = _DummyService(ai_manager=manager)

    result = await service._call_ai_manager_script(
        episode={"duration_minutes": 30, "scenes": original_scenes},
        story={"title": "T"},
        format_type="short_video",
        language="zh",
        dialogue_style="natural",
        scene_detail_level="medium",
        additional_requirements=None,
        style_preferences=None,
        model="minimax:abab",
        prefer_provider="minimax",
        temperature=0.7,
    )

    assert result is not None
    assert len(manager.calls) == 2
    assert manager.calls[0]["max_tokens"] == _SCENE_PLAN_MAX_TOKENS
    assert manager.calls[1]["max_tokens"] == _DIALOGUE_MAX_TOKENS
    assert manager.calls[0]["json_schema"]["name"] == "script_scenes"
    assert manager.calls[1]["json_schema"]["name"] == "script_dialogues"
