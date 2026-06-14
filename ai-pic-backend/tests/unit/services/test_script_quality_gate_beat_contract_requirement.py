from __future__ import annotations

from typing import Any

import pytest

from app.services.narrative_quality_gate import evaluate_script_quality_gate


def _script_content() -> dict[str, Any]:
    return {
        "content": "\n".join(
            [
                "【音效】砰！门被撞开。",
                "Scene 1 客厅 - 夜",
                "林雪抓住账本，警报声逼近。",
                "林雪：别动！账本上为什么有你的名字？",
                "陈默：不是我，有人改过它。",
            ]
        ),
        "scenes": [{"scene_number": 1, "description": "林雪在客厅逼问陈默。"}],
        "dialogues": [
            {
                "scene_number": 1,
                "character": "林雪",
                "content": "别动！账本上为什么有你的名字？",
            },
            {"scene_number": 1, "character": "陈默", "content": "有人改过它。"},
        ],
        "stage_directions": [
            {"scene_number": 1, "content": "林雪抓住账本，警报声逼近。"}
        ],
        "metadata": {},
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_gate_requires_beat_contract_when_requested() -> None:
    gate = await evaluate_script_quality_gate(
        content=_script_content(),
        story={"characters": [{"name": "林雪"}, {"name": "陈默"}]},
        result={},
        require_beat_contract=True,
    )

    blocking_ids = {issue["id"] for issue in gate["blocking_issues"]}
    assert "script_beat_contract_required" in blocking_ids


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_gate_does_not_require_beat_contract_by_default() -> None:
    gate = await evaluate_script_quality_gate(
        content=_script_content(),
        story={"characters": [{"name": "林雪"}, {"name": "陈默"}]},
        result={},
    )

    all_check_ids = {check["id"] for check in gate["checks"]}
    assert "script_beat_contract_required" not in all_check_ids
