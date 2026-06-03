from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from app.models.script import Story, StoryCharacter
from app.services.narrative_quality_gate import enforce_script_quality_gate_with_repair


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

    async def generate_text(self, **kwargs: Any) -> Any:
        schema = kwargs.get("json_schema") or {}
        if schema.get("name") == "script_cliffhanger_judgement":
            return SimpleNamespace(
                success=True,
                provider="fake",
                model="fake-model",
                data={
                    "passed": True,
                    "score": 1.0,
                    "reason": "ok",
                    "evidence": "tail",
                    "suggestion": "",
                },
            )
        self.calls += 1
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


def _story_model_with_registry() -> Story:
    story = Story(
        user_id=7,
        title="S",
        story_format="short_drama",
        genre="drama",
        default_aspect_ratio="9:16",
    )
    story.story_characters = [
        StoryCharacter(character_name="林雪", is_deleted=False),
        StoryCharacter(character_name="陈默", is_deleted=False),
    ]
    return story


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_gate_auto_creates_episode_temporary_speaker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = _script_content()
    content["scenes"][0]["characters"] = ["林雪", "快递员"]
    content["dialogues"].append(
        {"scene_number": 1, "character": "快递员", "content": "别动！"}
    )
    db = _EpisodeCharacterDb()

    async def fake_auto_create_episode_characters(
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        assert kwargs["unknown_names"] == ["快递员"]
        kwargs["db"].episode_chars.append(
            SimpleNamespace(
                character_name="快递员",
                virtual_ip=None,
                virtual_ip_id=99,
                is_deleted=False,
            )
        )
        return [{"episode_character_id": 123, "character_name": "快递员"}]

    monkeypatch.setattr(
        "app.services.script.auto_character_creator.auto_create_episode_characters",
        fake_auto_create_episode_characters,
    )

    result, updated_content, gate = await enforce_script_quality_gate_with_repair(
        ai_manager=_RepairManager([]),
        result={},
        content=content,
        story={"characters": [{"name": "林雪"}, {"name": "陈默"}]},
        story_model=_story_model_with_registry(),
        episode_id=55,
        db=db,
        lint_threshold=0.0,
    )

    assert gate["passed"] is True
    assert result["auto_created_characters"] == [
        {"episode_character_id": 123, "character_name": "快递员"}
    ]
    assert updated_content["dialogues"][-1]["character"] == "快递员"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_gate_rejects_repair_that_drops_script_structure() -> None:
    manager = _RepairManager(
        [
            {
                "content": "第3集",
                "scenes": [],
                "dialogues": [],
                "stage_directions": [],
                "metadata": {},
            },
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
    assert gate["repair_attempts"][0]["structure_guard"]["passed"] is False
    assert gate["repair_attempts"][0]["structure_guard"]["lost_fields"] == [
        "scenes",
        "dialogues",
        "stage_directions",
    ]
