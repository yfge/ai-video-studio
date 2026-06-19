from types import SimpleNamespace

import pytest
from app.services.quality_gate_repair import repair_quality_gate_payload


class _DummyAIManager:
    def __init__(self):
        self.calls = []

    async def generate_text(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(success=True, data={"repaired": True})


@pytest.mark.asyncio
@pytest.mark.unit
async def test_deepseek_v4_pro_quality_gate_repair_disables_thinking():
    manager = _DummyAIManager()

    repaired = await repair_quality_gate_payload(
        ai_manager=manager,
        kind="script",
        payload={"content": "短剧正文"},
        quality_gate={"passed": False},
        schema={"name": "script", "schema": {"type": "object"}},
        model="deepseek-v4-pro",
        prefer_provider="deepseek",
        temperature=0.7,
    )

    assert repaired == {"repaired": True}
    assert manager.calls[0]["thinking"] == {"type": "disabled"}


@pytest.mark.asyncio
@pytest.mark.unit
async def test_quality_gate_repair_includes_extra_instructions():
    manager = _DummyAIManager()

    await repair_quality_gate_payload(
        ai_manager=manager,
        kind="episode",
        payload={"episodes": [{"episode_number": 1}]},
        quality_gate={"passed": False},
        schema={"name": "episode_plan", "schema": {"type": "object"}},
        model="deepseek-v4-flash",
        prefer_provider="deepseek",
        temperature=0.7,
        extra_instructions="Every episode must include structured_episode_contract.",
    )

    prompt = manager.calls[0]["prompt"]
    assert "failed strict quality gate validation" in prompt
    assert "structured_episode_contract" in prompt
