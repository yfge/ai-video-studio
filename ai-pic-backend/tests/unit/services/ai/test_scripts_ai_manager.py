from __future__ import annotations

from typing import Any

import pytest
from app.services.ai.scripts_ai_manager import (
    _BEAT_CONTRACT_MAX_TOKENS,
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


def _beat_contract(scenes: list[dict[str, Any]]) -> dict[str, Any]:
    first = dict(scenes[0])
    return {
        "contract_version": "script-beat-v1",
        "title": "T",
        "logline": "A must stop the loss before the timer ends.",
        "scenes": [
            {
                "scene_number": first.get("scene_number", 1),
                "slug_line": first.get("slug_line") or "INT. Room - day",
                "location": first.get("location") or "room",
                "time_of_day": first.get("time_of_day") or "day",
                "estimated_duration_seconds": first.get(
                    "estimated_duration_seconds", 15
                ),
                "dramatic_role": "hook",
                "conflict": {
                    "question": "Who changed the timer?",
                    "stakes": "The prize is lost if A cannot prove it.",
                    "opposition": "A locked system.",
                    "turn": "The log deletes itself.",
                },
                "beats": [
                    {
                        "order_index": 1,
                        "beat_type": "hook",
                        "dramatic_purpose": "Show immediate loss.",
                        "visible_event": "The prize counter drops to zero.",
                        "action_lines": [{"content": "A runs to the console."}],
                        "dialogue_lines": [{"character": "A", "content": "Zero?"}],
                        "duration_seconds": 5,
                        "hook_tag": "loss",
                    },
                    {
                        "order_index": 2,
                        "beat_type": "conflict",
                        "dramatic_purpose": "Block the protagonist.",
                        "visible_event": "The console rejects A's access.",
                        "action_lines": [{"content": "The screen flashes red."}],
                        "dialogue_lines": [{"character": "A", "content": "Denied."}],
                        "duration_seconds": 5,
                    },
                    {
                        "order_index": 3,
                        "beat_type": "cliffhanger",
                        "dramatic_purpose": "Reveal a hidden operator.",
                        "visible_event": "A shadow erases the final log row.",
                        "action_lines": [{"content": "The last row vanishes."}],
                        "dialogue_lines": [{"character": "A", "content": "Who?"}],
                        "duration_seconds": 5,
                        "cliffhanger_tag": "hidden_operator",
                    },
                ],
            }
        ],
    }


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
            _DummyResponse(success=True, data=_beat_contract(planned_scenes)),
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
    assert result["content"]["structured_script_contract"]["contract_version"] == (
        "script-beat-v1"
    )

    assert len(manager.calls) == 3
    assert manager.calls[0]["max_tokens"] == _SCENE_PLAN_MAX_TOKENS
    assert manager.calls[1]["max_tokens"] == _BEAT_CONTRACT_MAX_TOKENS
    assert manager.calls[2]["max_tokens"] == _REPAIR_MAX_TOKENS
    assert manager.calls[0]["json_schema"]["name"] == "script_scenes"
    assert manager.calls[1]["json_schema"]["name"] == "script_beat_contract"
    assert manager.calls[2]["json_schema"]["name"] == "script_beat_contract"
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
            _DummyResponse(success=True, data=_beat_contract(planned_scenes)),
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
    assert manager.calls[1]["max_tokens"] == _BEAT_CONTRACT_MAX_TOKENS
    assert manager.calls[0]["json_schema"]["name"] == "script_scenes"
    assert manager.calls[1]["json_schema"]["name"] == "script_beat_contract"
