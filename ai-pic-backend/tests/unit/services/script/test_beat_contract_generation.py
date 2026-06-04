from __future__ import annotations

from typing import Any

import pytest
from app.services.script.beat_contract_generation import (
    BeatContractGenerationError,
    generate_beat_contract_payload,
)


class _DummyResponse:
    def __init__(
        self,
        *,
        success: bool = True,
        data: Any = None,
        provider: str = "deepseek",
        model: str = "deepseek-v4-pro",
        usage: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        self.success = success
        self.data = data
        self.provider = provider
        self.model = model
        self.usage = usage or {}
        self.metadata = metadata or {}
        self.error = error


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
async def test_deepseek_v4_pro_beat_contract_disables_thinking_for_json_calls():
    manager = _DummyManager([_DummyResponse(data=_contract_payload())])

    result = await _generate(manager)

    assert result["payload"]["structured_script_contract"]["contract_version"] == (
        "script-beat-v1"
    )
    assert manager.calls[0]["thinking"] == {"type": "disabled"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalid_json_error_reports_deepseek_token_diagnostics():
    manager = _DummyManager(
        [
            _DummyResponse(
                data='{"contract_version":"script-beat-v1","scenes":[',
                usage={
                    "completion_tokens": 6000,
                    "completion_tokens_details": {"reasoning_tokens": 2383},
                },
                metadata={"finish_reason": "length"},
            ),
            _DummyResponse(
                data='{"contract_version":"script-beat-v1","scenes":[',
                usage={
                    "completion_tokens": 4096,
                    "completion_tokens_details": {"reasoning_tokens": 3254},
                },
                metadata={"finish_reason": "length"},
            ),
        ]
    )

    with pytest.raises(BeatContractGenerationError) as exc_info:
        await _generate(manager)

    assert exc_info.value.code == "beat_contract_invalid_json"
    message = str(exc_info.value)
    assert "provider=deepseek" in message
    assert "model=deepseek-v4-pro" in message
    assert "finish_reason=length" in message
    assert "max_tokens=6000" in message
    assert "completion_tokens=4096" in message
    assert "reasoning_tokens=3254" in message
    assert manager.calls[0]["thinking"] == {"type": "disabled"}
    assert manager.calls[1]["thinking"] == {"type": "disabled"}
    assert manager.calls[1]["max_tokens"] == manager.calls[0]["max_tokens"]
