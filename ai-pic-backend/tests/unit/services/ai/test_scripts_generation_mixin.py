from __future__ import annotations

import asyncio
import logging
from typing import Any

import pytest
from app.services.ai import scripts as scripts_module
from app.services.ai.scripts import ScriptGenerationMixin


class _DummyAgent:
    def __init__(self) -> None:
        self.kwargs: dict[str, Any] | None = None

    async def generate(self, **kwargs: Any):
        self.kwargs = kwargs
        await asyncio.sleep(1)
        return {"content": {"scenes": [], "dialogues": [], "stage_directions": []}}


class _DummyService(ScriptGenerationMixin):
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.script_agent = _DummyAgent()
        self.direct_called = False

    async def _call_ai_manager_script(self, **_: Any):
        self.direct_called = True
        return {
            "content": {"scenes": [], "dialogues": [], "stage_directions": []},
            "normalized": {"scenes": [], "dialogues": [], "stage_directions": []},
        }

    async def _generate_mock_script(self, **_: Any):
        raise AssertionError("mock fallback should not be used")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_script_times_out_and_falls_back_to_direct(monkeypatch):
    service = _DummyService()
    monkeypatch.setattr(scripts_module, "_SCRIPT_AGENT_TIMEOUT_SECONDS", 0.01)

    result = await service.generate_script(episode={}, story={})

    assert result is not None
    assert service.script_agent.kwargs is not None
    assert service.script_agent.kwargs["duration_minutes"] == 0
    assert service.direct_called is True
    assert result["content"]["content"].startswith("# screenplay")
