from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from app.services.narrative_quality_gate import evaluate_script_quality_gate


class _PassingCliffhangerManager:
    async def generate_text(self, **kwargs: Any) -> Any:
        return SimpleNamespace(
            success=True,
            data={
                "passed": True,
                "score": 1.0,
                "reason": "ok",
                "evidence": "tail",
                "suggestion": "",
            },
            provider=kwargs.get("prefer_provider") or "fake",
            model=kwargs.get("model") or "fake-model",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_gate_blocks_fallback_dialogue_content() -> None:
    content = {
        "content": "\n".join(
            [
                "【音效】砰！门被撞开。",
                "Scene 1 客厅 - 夜",
                "【快】【情绪目的：逼出真相】林雪抓住账本。",
                "林雪：那真正签字的人是谁？",
            ]
        ),
        "scenes": [{"scene_number": 1, "description": "林雪在客厅逼问陈默。"}],
        "dialogues": [
            {
                "scene_number": 1,
                "character": "旁白",
                "content": "林雪在客厅逼问陈默。",
                "fallback": True,
                "fallback_reason": "missing_dialogues",
            }
        ],
        "stage_directions": [{"scene_number": 1, "content": "林雪抓住账本。"}],
        "metadata": {},
    }

    gate = await evaluate_script_quality_gate(
        content=content,
        story={"characters": [{"name": "林雪"}, {"name": "陈默"}]},
        result={},
        ai_manager=_PassingCliffhangerManager(),
    )

    blocking_ids = {issue["id"] for issue in gate["blocking_issues"]}
    assert "script_dialogue_fallback" in blocking_ids
