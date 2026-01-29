from __future__ import annotations

import pytest
from app.models.script import Story, StoryCharacter
from app.models.virtual_ip import VirtualIP
from app.services.script.script_character_policy import enforce_script_character_policy


def _make_story_with_registry() -> Story:
    story = Story(
        user_id=1,
        title="S",
        story_format="short_drama",
        genre="drama",
        default_aspect_ratio="9:16",
    )

    vip_male = VirtualIP(user_id=1, name="短剧E2E男主-陈哲")
    vip_female = VirtualIP(user_id=1, name="短剧E2E女主-林雪-2026-01-19T03-52-25-958Z")

    sc_male = StoryCharacter(
        story_id=1,
        virtual_ip_id=1,
        character_name="陈哲",
        is_deleted=False,
    )
    sc_male.virtual_ip = vip_male

    # character_name intentionally omitted to cover preferred_display_name(vip.name).
    sc_female = StoryCharacter(
        story_id=1,
        virtual_ip_id=2,
        character_name=None,
        is_deleted=False,
    )
    sc_female.virtual_ip = vip_female

    story.story_characters = [sc_male, sc_female]
    return story


@pytest.mark.unit
def test_enforce_script_character_policy_normalizes_and_detects_unknown() -> None:
    story = _make_story_with_registry()
    scenes = [{"characters": ["小雪", "路人甲", "反派老拐"]}]
    dialogues = [{"character": "店员A", "content": "你好"}, {"content": "旁白内容"}]

    result = enforce_script_character_policy(
        story=story, scenes=scenes, dialogues=dialogues
    )

    assert result.unknown_names == ["反派老拐"]
    assert set(result.canonical_names) == {"陈哲", "林雪"}
    assert result.normalized_count >= 1

    assert scenes[0]["characters"] == ["林雪", "路人", "反派老拐"]
    assert dialogues[0]["character"] == "店员"
    assert dialogues[1]["character"] == "旁白"


@pytest.mark.unit
def test_enforce_script_character_policy_is_backwards_compatible_without_registry() -> (
    None
):
    story = Story(
        user_id=1,
        title="S",
        story_format="short_drama",
        genre="drama",
        default_aspect_ratio="9:16",
    )
    story.story_characters = []

    scenes = [{"characters": ["陈哲"]}]
    dialogues = [{"content": "没有 speaker 时应默认旁白"}]

    result = enforce_script_character_policy(
        story=story, scenes=scenes, dialogues=dialogues
    )

    assert result.unknown_names == []
    assert result.canonical_names == []
    assert result.normalized_count == 0
    assert dialogues[0]["character"] == "旁白"
