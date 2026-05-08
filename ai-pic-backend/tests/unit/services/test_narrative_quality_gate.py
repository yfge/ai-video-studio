from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.services.narrative_quality_gate import (
    NarrativeQualityGateError,
    attach_quality_gate_failure_to_task,
    build_quality_gate_report,
    enforce_episode_quality_gate_with_repair,
    enforce_script_quality_gate_with_repair,
    evaluate_episode_quality_gate,
    evaluate_script_quality_gate,
    make_quality_check,
)
from app.services.quality_gate_core import QUALITY_GATE_ERROR_CODE


def _episode(number: int = 1, *, character_name: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "episode_number": number,
        "title": f"第{number}集",
        "summary": "林雪发现账本里的秘密，危机升级。",
        "plot_points": [{"description": "林雪夺到账本，陈默追上来。"}],
        "conflicts": [{"description": "林雪和陈默争夺账本", "intensity": "high"}],
        "scene_count": 1,
        "scenes": [
            {
                "scene_number": 1,
                "slug_line": "Scene 1",
                "summary": "林雪夺到账本。",
            }
        ],
    }
    if character_name:
        payload["characters"] = [{"name": character_name}]
    return payload


def _script_content(text: str | None = None) -> dict[str, Any]:
    return {
        "content": text or _passing_script_text(),
        "scenes": [
            {
                "scene_number": 1,
                "description": "林雪在客厅逼问陈默。",
            }
        ],
        "dialogues": [
            {
                "scene_number": 1,
                "character": "林雪",
                "content": "别动！账本上为什么有你的名字？",
            },
            {
                "scene_number": 1,
                "character": "陈默",
                "content": "不是我，嗯...有人改过它。",
            },
        ],
        "stage_directions": [
            {
                "scene_number": 1,
                "content": "林雪抓住账本，警报声逼近。",
            }
        ],
        "metadata": {},
    }


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


class _RepairManager:
    def __init__(
        self,
        payloads: list[dict[str, Any]],
        *,
        cliffhanger_passes: list[bool] | None = None,
    ) -> None:
        self.payloads = list(payloads)
        self.cliffhanger_passes = list(cliffhanger_passes or [])
        self.calls = 0
        self.cliffhanger_calls = 0

    async def generate_text(self, **kwargs: Any) -> Any:
        schema = kwargs.get("json_schema") or {}
        if schema.get("name") == "script_cliffhanger_judgement":
            self.cliffhanger_calls += 1
            passed = (
                self.cliffhanger_passes.pop(0)
                if self.cliffhanger_passes
                else True
            )
            return SimpleNamespace(
                success=True,
                provider=kwargs.get("prefer_provider") or "fake",
                model=kwargs.get("model") or "fake-model",
                data={
                    "passed": passed,
                    "score": 1.0 if passed else 0.0,
                    "reason": "ok" if passed else "weak ending",
                    "evidence": "tail",
                    "suggestion": "补强结尾卡点",
                },
            )
        self.calls += 1
        payload = self.payloads.pop(0) if self.payloads else {}
        return SimpleNamespace(success=True, data=payload)


@pytest.mark.unit
def test_quality_gate_report_blocks_error_checks() -> None:
    gate = build_quality_gate_report(
        kind="script",
        checks=[
            make_quality_check("ok", True, "ok"),
            make_quality_check("bad", False, "blocking"),
            make_quality_check("warn", False, "warning", severity="warning"),
        ],
    )

    assert gate["passed"] is False
    assert gate["score"] < 10
    assert [issue["id"] for issue in gate["blocking_issues"]] == ["bad"]
    assert [warning["id"] for warning in gate["warnings"]] == ["warn"]


@pytest.mark.unit
def test_episode_gate_blocks_unknown_character() -> None:
    gate = evaluate_episode_quality_gate(
        episodes=[_episode(character_name="陌生人")],
        story={"characters": [{"name": "林雪"}]},
        episode_count=1,
    )

    assert gate["passed"] is False
    assert any(issue["id"] == "episode_characters" for issue in gate["blocking_issues"])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_episode_gate_repairs_for_two_rounds_then_passes() -> None:
    manager = _RepairManager(
        [
            {"episodes": []},
            {"episodes": [_episode()]},
        ]
    )

    result = await enforce_episode_quality_gate_with_repair(
        ai_manager=manager,
        result={"normalized": {"episodes": []}},
        story={"characters": [{"name": "林雪"}]},
        episode_count=1,
    )

    assert result["quality_gate"]["passed"] is True
    assert manager.calls == 2
    assert len(result["quality_gate"]["repair_attempts"]) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_gate_blocks_low_lint_score_and_unknown_speaker() -> None:
    content = _script_content("普通文本，没有生产标记，也没有悬念结尾。")
    content["dialogues"][0]["character"] = "陌生人"
    gate = await evaluate_script_quality_gate(
        content=content,
        story={"characters": [{"name": "林雪"}, {"name": "陈默"}]},
        result={},
        ai_manager=_RepairManager([], cliffhanger_passes=[False]),
    )

    blocking_ids = {issue["id"] for issue in gate["blocking_issues"]}
    assert "script_lint" in blocking_ids
    assert "script_characters" in blocking_ids


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_gate_repairs_for_two_rounds_then_passes() -> None:
    manager = _RepairManager(
        [
            _script_content("仍然没有钩子和悬念。"),
            _script_content(),
        ]
    )

    result, content, gate = await enforce_script_quality_gate_with_repair(
        ai_manager=manager,
        result={},
        content=_script_content("坏文本。"),
        story={"characters": [{"name": "林雪"}, {"name": "陈默"}]},
    )

    assert gate["passed"] is True
    assert result["quality_gate"]["passed"] is True
    assert content["content"] == _passing_script_text()
    assert manager.calls == 2
    assert len(gate["repair_attempts"]) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_quality_gate_raises_after_repair_budget_exhausted() -> None:
    manager = _RepairManager([_script_content("坏文本。"), _script_content("仍然坏。")])

    with pytest.raises(NarrativeQualityGateError) as exc_info:
        await enforce_script_quality_gate_with_repair(
            ai_manager=manager,
            result={},
            content=_script_content("坏文本。"),
            story={"characters": [{"name": "林雪"}, {"name": "陈默"}]},
        )

    assert exc_info.value.quality_gate["passed"] is False
    assert len(exc_info.value.quality_gate["repair_attempts"]) == 2


@pytest.mark.unit
def test_attach_quality_gate_failure_to_task_records_error_code() -> None:
    task = SimpleNamespace(parameters='{"agent_run":{"existing":true}}')
    gate = build_quality_gate_report(
        kind="episode",
        checks=[make_quality_check("bad", False, "blocking")],
    )

    attach_quality_gate_failure_to_task(task, gate)

    assert QUALITY_GATE_ERROR_CODE in task.parameters
    assert '"existing": true' in task.parameters
    assert '"quality_gate"' in task.parameters
