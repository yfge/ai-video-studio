from __future__ import annotations

import asyncio
import logging
from typing import Any

import pytest
from app.services.ai import scripts as scripts_module
from app.services.ai.scripts import ScriptGenerationMixin
from app.services.duration_orchestrator.state import SceneBudget


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

    ledger = {"facts": ["A knows B"]}
    result = await service.generate_script(
        episode={"duration_minutes": 2},
        story={"continuity_ledger": ledger},
    )

    assert result is not None
    assert service.script_agent.kwargs is not None
    assert service.script_agent.kwargs["duration_minutes"] is None
    assert service.script_agent.kwargs["continuity_ledger"] == ledger
    assert service.direct_called is True
    assert result["content"]["content"].startswith("# screenplay")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_script_keeps_external_scene_budgets_authoritative(monkeypatch):
    service = _DummyService()
    monkeypatch.setattr(scripts_module, "_SCRIPT_AGENT_TIMEOUT_SECONDS", 0.01)
    budgets = [
        SceneBudget(
            scene_number=1,
            scene_index=0,
            target_duration_seconds=60,
            target_word_count=120,
            min_duration_seconds=50,
            max_duration_seconds=70,
        )
    ]

    result = await service.generate_script(
        episode={"duration_minutes": 2},
        story={},
        scene_budgets=budgets,
    )

    assert result is not None
    assert service.script_agent.kwargs is not None
    assert service.script_agent.kwargs["scene_budgets"] == budgets
    assert service.script_agent.kwargs["duration_minutes"] == 0
