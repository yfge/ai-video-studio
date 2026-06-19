from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from app.models.script import Story, StoryCharacter
from app.services.narrative_quality_gate import enforce_script_quality_gate_with_repair
from app.services.quality_gate_core import NarrativeQualityGateError


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
            {"scene_number": 1, "character": "林雪", "content": "别动！"},
            {"scene_number": 1, "character": "陈默", "content": "不是我，嗯..."},
        ],
        "stage_directions": [{"scene_number": 1, "content": "林雪抓住账本。"}],
        "metadata": {},
    }


class _RepairManager:
    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self.payloads = list(payloads)
        self.calls = 0
        self.call_kwargs: list[dict[str, Any]] = []

    async def generate_text(self, **kwargs: Any) -> Any:
        schema = kwargs.get("json_schema") or {}
        if schema.get("name") == "script_cliffhanger_judgement":
            return SimpleNamespace(
                success=True,
                provider="fake",
                model="fake-model",
                data={"passed": True, "score": 1.0, "reason": "ok"},
            )
        self.calls += 1
        self.call_kwargs.append(kwargs)
        payload = self.payloads.pop(0) if self.payloads else {}
        return SimpleNamespace(success=True, data=payload)


class _EpisodeCharacterQuery:
    def __init__(self, rows: list[Any]) -> None:
        self.rows = rows

    def filter(self, *args: Any, **kwargs: Any) -> "_EpisodeCharacterQuery":
        return self

    def all(self) -> list[Any]:
        return list(self.rows)


class _EpisodeCharacterDb:
    def __init__(self) -> None:
        self.episode_chars: list[Any] = []

    def query(self, model: Any) -> _EpisodeCharacterQuery:
        return _EpisodeCharacterQuery(self.episode_chars)


def _story_model_with_ap_registry() -> Story:
    story = Story(user_id=7, title="S", story_format="short_drama", genre="drama")
    story.default_aspect_ratio = "9:16"
    story.story_characters = [StoryCharacter(character_name="AP", is_deleted=False)]
    return story


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_gate_refreshes_stale_unknown_speaker_flag_without_creation() -> None:
    content = {
        "content": _passing_script_text(),
        "scenes": [{"scene_number": 1, "description": "AP查看短信。"}],
        "dialogues": [
            {"scene_number": 1, "character": "AP", "content": "证据在这。"},
            {"scene_number": 1, "character": "短信", "content": "下一个就是你。"},
        ],
        "stage_directions": [{"scene_number": 1, "content": "AP举起手机。"}],
        "metadata": {},
    }

    result, _content, gate = await enforce_script_quality_gate_with_repair(
        ai_manager=_RepairManager([]),
        result={
            "character_validation_passed": False,
            "character_validation_results": [
                {
                    "passed": False,
                    "severity": "warning",
                    "message": "Found 2 unknown speaker(s) in dialogues",
                    "details": {"unknown_speakers": ["AP", "短信"]},
                }
            ],
            "character_warnings": ["Unknown speaker(s) in dialogues: AP, 短信"],
            "unknown_names": ["AP", "短信"],
        },
        content=content,
        story={"characters": [{"name": "AP"}]},
        story_model=_story_model_with_ap_registry(),
        episode_id=55,
        db=_EpisodeCharacterDb(),
        lint_threshold=0.0,
    )

    assert gate["passed"] is True
    assert result["character_validation_passed"] is True
    assert result["unknown_names"] == []
    assert "auto_created_characters" not in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_gate_repair_uses_generation_provider_for_auto_model() -> None:
    manager = _RepairManager([_script_content()])

    result, _content, gate = await enforce_script_quality_gate_with_repair(
        ai_manager=manager,
        result={"provider_used": "deepseek", "model_used": "deepseek-v4-flash"},
        content=_script_content("坏文本。"),
        story={"characters": [{"name": "林雪"}, {"name": "陈默"}]},
    )

    assert gate["passed"] is True
    assert result["quality_gate"]["passed"] is True
    assert manager.calls == 1
    assert manager.call_kwargs[0]["prefer_provider"] == "deepseek"
    assert manager.call_kwargs[0]["model"] == "deepseek-v4-flash"
    assert "Return the repaired script payload itself" not in manager.call_kwargs[0][
        "prompt"
    ]
    assert "Every structured_script_contract.scenes item" not in manager.call_kwargs[0][
        "prompt"
    ]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_gate_beat_contract_repair_prompt_is_payload_specific() -> None:
    manager = _RepairManager([_script_content()])

    with pytest.raises(NarrativeQualityGateError):
        await enforce_script_quality_gate_with_repair(
            ai_manager=manager,
            result={"provider_used": "deepseek", "model_used": "deepseek-v4-flash"},
            content=_script_content("坏文本。"),
            story={"characters": [{"name": "林雪"}, {"name": "陈默"}]},
            require_beat_contract=True,
        )

    prompt = manager.call_kwargs[0]["prompt"]
    assert manager.call_kwargs[0]["prefer_provider"] == "deepseek"
    assert manager.call_kwargs[0]["model"] == "deepseek-v4-flash"
    assert "Return the repaired script payload itself" in prompt
    assert "Every structured_script_contract.scenes item" in prompt
    assert "duration_seconds values in each scene must sum" in prompt
