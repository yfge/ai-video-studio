from __future__ import annotations

from typing import Any

import pytest
from app.services.script.beat_contract_generation import generate_beat_contract_payload


class _DummyResponse:
    def __init__(
        self,
        *,
        data: Any = None,
        provider: str = "deepseek",
        model: str = "deepseek-v4-pro",
    ) -> None:
        self.success = True
        self.data = data
        self.provider = provider
        self.model = model
        self.usage = {}
        self.metadata = {}
        self.error = None


class _DummyManager:
    def __init__(self, responses: list[_DummyResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    async def generate_text(self, **kwargs: Any) -> _DummyResponse:
        self.calls.append(kwargs)
        return self.responses.pop(0)


def _contract_payload() -> dict[str, Any]:
    return {
        "contract_version": "script-beat-v1",
        "title": "T",
        "scenes": [
            {
                "scene_number": 1,
                "slug_line": "INT. Room - day",
                "dramatic_role": "hook",
                "conflict": {
                    "question": "Who framed A?",
                    "stakes": "A loses everything.",
                    "opposition": "A false recording.",
                    "turn": "The real voice appears.",
                },
                "beats": [
                    {
                        "order_index": 1,
                        "beat_type": "hook",
                        "dramatic_purpose": "Open with public accusation.",
                        "visible_event": "A stranger plays a recording.",
                        "action_lines": [{"content": "The room turns silent."}],
                        "dialogue_lines": [{"character": "A", "content": "Stop."}],
                    }
                ],
            }
        ],
    }


async def _generate(manager: _DummyManager) -> dict[str, Any]:
    return await generate_beat_contract_payload(
        manager,
        episode={"episode_number": 1, "title": "Episode"},
        story={"title": "Story"},
        scenes=[{"scene_number": 1, "slug_line": "INT. Room - day"}],
        format_type="screenplay",
        language="zh-CN",
        dialogue_style="natural",
        template_style="commercial_vertical_drama",
        target_chars_per_episode=1300,
        quality_threshold=9.0,
        additional_requirements=None,
        temperature=0.7,
        model="deepseek-v4-pro",
        prefer_provider="deepseek",
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_beat_contract_generation_accepts_common_role_aliases():
    payload = _contract_payload()
    payload["scenes"][0]["dramatic_role"] = "conflict_ladder"
    payload["scenes"][0]["beats"][0]["beat_type"] = "progressive"
    manager = _DummyManager([_DummyResponse(data=payload)])

    result = await _generate(manager)

    contract = result["payload"]["structured_script_contract"]
    assert contract["scenes"][0]["dramatic_role"] == "escalation"
    assert contract["scenes"][0]["beats"][0]["beat_type"] == "conflict"
    assert len(manager.calls) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_beat_contract_generation_defaults_unknown_non_empty_labels():
    payload = _contract_payload()
    payload["scenes"][0]["dramatic_role"] = "mystery_phase"
    payload["scenes"][0]["beats"][0]["beat_type"] = "surprise_move"
    manager = _DummyManager([_DummyResponse(data=payload)])

    result = await _generate(manager)

    contract = result["payload"]["structured_script_contract"]
    assert contract["scenes"][0]["dramatic_role"] == "escalation"
    assert contract["scenes"][0]["beats"][0]["beat_type"] == "conflict"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_beat_contract_generation_repairs_parsed_invalid_contract():
    invalid_payload = _contract_payload()
    invalid_payload["scenes"][0].pop("conflict")
    manager = _DummyManager(
        [
            _DummyResponse(data=invalid_payload),
            _DummyResponse(data=_contract_payload(), provider="openai", model="gpt-4o"),
        ]
    )

    result = await _generate(manager)

    assert result["payload"]["structured_script_contract"]["contract_version"] == (
        "script-beat-v1"
    )
    assert result["response"].provider == "openai"
    assert len(manager.calls) == 2
