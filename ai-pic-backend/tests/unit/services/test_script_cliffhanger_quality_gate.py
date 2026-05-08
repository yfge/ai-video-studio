from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.services.narrative_quality_gate import (
    NarrativeQualityGateError,
    enforce_script_quality_gate_with_repair,
)


def _passing_script_text() -> str:
    return "\n".join(
        [
            "【音效】砰！门被撞开。",
            "Scene 1 客厅 - 夜",
            "【快】【情绪目的：逼出真相】林雪抓住账本，镜头推近她发抖的手。",
            "【音效】警报声从窗外逼近。",
            "林雪：别动！账本上为什么有你的名字？",
            "陈默：不是我，嗯...有人改过它。",
            "（动作）陈默后退半步，杯子落地。",
            "Scene 2 天台 - 夜",
            "【慢】【情绪目的：制造反转】林雪把账本举到灯下，红色签名露出。",
            "陈默：你看最后一页。",
            "林雪：那真正签字的人是谁？",
        ]
    )


def _script_content(text: str | None = None) -> dict[str, Any]:
    return {
        "content": text or _passing_script_text(),
        "scenes": [{"scene_number": 1, "description": "林雪在客厅逼问陈默。"}],
        "dialogues": [
            {"scene_number": 1, "character": "林雪", "content": "别动！账本上为什么有你的名字？"},
            {"scene_number": 1, "character": "陈默", "content": "不是我，嗯...有人改过它。"},
        ],
        "stage_directions": [{"scene_number": 1, "content": "林雪抓住账本，警报声逼近。"}],
        "metadata": {},
    }


class _RepairManager:
    def __init__(
        self,
        payloads: list[dict[str, Any]],
        *,
        cliffhanger_passes: list[bool],
    ) -> None:
        self.payloads = list(payloads)
        self.cliffhanger_passes = list(cliffhanger_passes)
        self.calls = 0
        self.cliffhanger_calls = 0

    async def generate_text(self, **kwargs: Any) -> Any:
        schema = kwargs.get("json_schema") or {}
        if schema.get("name") == "script_cliffhanger_judgement":
            self.cliffhanger_calls += 1
            passed = self.cliffhanger_passes.pop(0)
            return SimpleNamespace(
                success=True,
                provider=kwargs.get("prefer_provider") or "fake",
                model=kwargs.get("model") or "fake-model",
                data={
                    "passed": passed,
                    "score": 1.0 if passed else 0.8,
                    "reason": "ok" if passed else "weak ending",
                    "evidence": "tail",
                    "suggestion": "补强结尾卡点",
                },
            )
        self.calls += 1
        payload = self.payloads.pop(0) if self.payloads else {}
        return SimpleNamespace(success=True, data=payload)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_gate_repairs_when_cliffhanger_prompt_fails() -> None:
    manager = _RepairManager([_script_content()], cliffhanger_passes=[False, True])

    result, _content, gate = await enforce_script_quality_gate_with_repair(
        ai_manager=manager,
        result={},
        content=_script_content(),
        story={"characters": [{"name": "林雪"}, {"name": "陈默"}]},
        model="deepseek:deepseek-v4-flash",
        prefer_provider="deepseek",
    )

    assert gate["passed"] is True
    assert result["quality_gate"]["passed"] is True
    assert manager.calls == 1
    assert manager.cliffhanger_calls == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_gate_blocks_when_cliffhanger_llm_unavailable() -> None:
    with pytest.raises(NarrativeQualityGateError) as exc_info:
        await enforce_script_quality_gate_with_repair(
            ai_manager=None,
            result={},
            content=_script_content(),
            story={"characters": [{"name": "林雪"}, {"name": "陈默"}]},
            max_repairs=0,
        )

    lint_issue = next(
        issue
        for issue in exc_info.value.quality_gate["blocking_issues"]
        if issue["id"] == "script_lint"
    )
    cliffhanger_rule = next(
        rule
        for rule in lint_issue["details"]["rules"]
        if rule["rule_id"] == "cliffhanger"
    )
    assert cliffhanger_rule["details"]["error"] == "cliffhanger_llm_unavailable"
